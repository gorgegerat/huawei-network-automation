import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database import Device, DeviceMetric, Alert, get_db
from services.huawei_device_service import HuaweiDeviceService
from services.notification_service import NotificationService
from pathlib import Path

# 配置日志
log_dir = Path(__file__).parent.parent.parent / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MonitorService:
    """监控服务 - 定期收集设备指标并检测异常"""

    def __init__(self, config: Dict[str, Any], notification_service: Optional[NotificationService]):
        self.config = config
        self.notification_service = notification_service
        self.scheduler = AsyncIOScheduler()
        self.device_service = HuaweiDeviceService()
        self.monitoring_config = config.get("monitoring", {})
        self._stop_flag = False
        self._current_task = None
    
    async def start(self):
        """启动监控服务"""
        check_interval = self.monitoring_config.get("check_interval", 60)

        # 添加定时任务
        self.scheduler.add_job(
            self.monitor_all_devices,
            'interval',
            seconds=check_interval,
            id='monitor_all_devices'
        )

        self.scheduler.start()
        logger.info(f"监控服务已启动，检查间隔: {check_interval}秒")
    
    async def stop(self):
        """停止监控服务"""
        self._stop_flag = True
        # 等待当前任务完成
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            try:
                await self._current_task
            except asyncio.CancelledError:
                pass
        self.scheduler.shutdown()
        logger.info("监控服务已停止")

    async def force_stop(self):
        """强制停止监控任务"""
        self._stop_flag = True
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            try:
                await self._current_task
            except asyncio.CancelledError:
                pass
        # 移除所有定时任务
        self.scheduler.remove_all_jobs()
        logger.warning("监控任务已强制停止")

    def is_running(self) -> bool:
        """检查监控服务是否正在运行"""
        return self.scheduler.running

    def get_current_task_status(self) -> Dict[str, Any]:
        """获取当前任务状态"""
        return {
            "running": self.scheduler.running,
            "has_active_task": self._current_task is not None and not self._current_task.done(),
            "stop_flag": self._stop_flag
        }
    
    async def monitor_all_devices(self):
        """监控所有设备"""
        db = next(get_db())
        try:
            devices = db.query(Device).filter(Device.status == "online").all()
            logger.info(f"开始监控 {len(devices)} 个在线设备")

            for device in devices:
                try:
                    logger.info(f"开始监控设备: {device.name} ({device.ip_address})")
                    await self.collect_device_metrics(device)
                    await self.check_device_health(device, db)
                    logger.info(f"设备 {device.name} 监控完成")
                except Exception as e:
                    logger.error(f"监控设备 {device.name} 失败: {str(e)}", exc_info=True)
                    # 创建设备离线告警
                    await self.create_alert(
                        db, device, "device_offline", "critical",
                        f"设备 {device.name} 监控失败",
                        f"设备 {device.name} ({device.ip_address}) 监控失败: {str(e)}"
                    )
            logger.info(f"监控周期完成，共处理 {len(devices)} 个设备")
        finally:
            db.close()
    
    async def collect_device_metrics(self, device: Device):
        """收集设备指标"""
        try:
            logger.info(f"开始收集设备 {device.name} 的指标")
            metrics = await self.device_service.get_metrics(device)
            logger.info(f"设备 {device.name} 指标收集成功: {metrics}")

            db = next(get_db())
            try:
                # 保存CPU指标
                if 'cpu' in metrics:
                    db.add(DeviceMetric(
                        device_id=device.id,
                        metric_type="cpu",
                        metric_value=metrics['cpu'],
                        unit="%"
                    ))
                    logger.debug(f"设备 {device.name} CPU指标已保存: {metrics['cpu']}%")

                # 保存内存指标
                if 'memory' in metrics:
                    db.add(DeviceMetric(
                        device_id=device.id,
                        metric_type="memory",
                        metric_value=metrics['memory'],
                        unit="%"
                    ))
                    logger.debug(f"设备 {device.name} 内存指标已保存: {metrics['memory']}%")

                # 保存接口指标（简化处理）
                if 'interfaces' in metrics:
                    logger.debug(f"设备 {device.name} 接口指标: {metrics['interfaces']}")

                db.commit()
            finally:
                db.close()

            # 更新设备最后在线时间
            db = next(get_db())
            try:
                device.last_seen = datetime.now(timezone.utc)
                db.commit()
                logger.debug(f"设备 {device.name} 最后在线时间已更新")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"收集设备 {device.name} 指标失败: {str(e)}", exc_info=True)
            raise
    
    async def check_device_health(self, device: Device, db: Session):
        """检查设备健康状态"""
        try:
            logger.info(f"开始检查设备 {device.name} 的健康状态")
            health = await self.device_service.check_health(device)
            logger.info(f"设备 {device.name} 健康检查结果: {health}")

            # 检查CPU使用率
            cpu_threshold = self.monitoring_config.get("cpu_threshold", 80)
            if 'cpu' in health and health['cpu'] > cpu_threshold:
                logger.warning(f"设备 {device.name} CPU使用率过高: {health['cpu']}% (阈值: {cpu_threshold}%)")
                await self.create_alert(
                    db, device, "high_cpu", "warning",
                    f"设备 {device.name} CPU使用率过高",
                    f"设备 {device.name} CPU使用率达到 {health['cpu']}%，超过阈值 {cpu_threshold}%"
                )

            # 检查内存使用率
            memory_threshold = self.monitoring_config.get("memory_threshold", 85)
            if 'memory' in health and health['memory'] > memory_threshold:
                logger.warning(f"设备 {device.name} 内存使用率过高: {health['memory']}% (阈值: {memory_threshold}%)")
                await self.create_alert(
                    db, device, "high_memory", "warning",
                    f"设备 {device.name} 内存使用率过高",
                    f"设备 {device.name} 内存使用率达到 {health['memory']}%，超过阈值 {memory_threshold}%"
                )

            # 检查健康问题
            if health.get("status") == "warning" and health.get("issues"):
                logger.warning(f"设备 {device.name} 存在健康问题: {health['issues']}")
                for issue in health["issues"]:
                    await self.create_alert(
                        db, device, "health_warning", "warning",
                        f"设备 {device.name} 健康警告",
                        issue
                    )

            # 发送通知
            if self.notification_service and health.get("issues"):
                await self.notification_service.send_alert(
                    "health_warning",
                    "warning",
                    f"设备 {device.name} 健康警告",
                    "\n".join(health["issues"])
                )
                logger.info(f"设备 {device.name} 健康警告通知已发送")

        except Exception as e:
            logger.error(f"检查设备 {device.name} 健康状态失败: {str(e)}", exc_info=True)
    
    async def create_alert(
        self,
        db: Session,
        device: Optional[Device],
        alert_type: str,
        severity: str,
        title: str,
        message: str
    ):
        """创建告警"""
        logger.info(f"创建告警: {alert_type} - {title} (严重性: {severity})")
        alert = Alert(
            device_id=device.id if device else None,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message
        )
        db.add(alert)
        db.commit()
        logger.info(f"告警已保存到数据库: {alert_type}")

        # 发送通知
        if self.notification_service and severity in ["critical", "warning"]:
            await self.notification_service.send_alert(alert_type, severity, title, message)
            logger.info(f"告警通知已发送: {alert_type}")

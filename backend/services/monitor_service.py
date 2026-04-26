import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from database import Device, DeviceMetric, Alert, get_db
from services.huawei_device_service import HuaweiDeviceService
from services.notification_service import NotificationService

class MonitorService:
    """监控服务 - 定期收集设备指标并检测异常"""
    
    def __init__(self, config: Dict[str, Any], notification_service: Optional[NotificationService]):
        self.config = config
        self.notification_service = notification_service
        self.scheduler = AsyncIOScheduler()
        self.device_service = HuaweiDeviceService()
        self.monitoring_config = config.get("monitoring", {})
    
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
        print("监控服务已启动")
    
    async def stop(self):
        """停止监控服务"""
        self.scheduler.shutdown()
        print("监控服务已停止")
    
    async def monitor_all_devices(self):
        """监控所有设备"""
        db = next(get_db())
        try:
            devices = db.query(Device).filter(Device.status == "online").all()
            
            for device in devices:
                try:
                    await self.collect_device_metrics(device)
                    await self.check_device_health(device, db)
                except Exception as e:
                    print(f"监控设备 {device.name} 失败: {str(e)}")
                    # 创建设备离线告警
                    await self.create_alert(
                        db, device, "device_offline", "critical",
                        f"设备 {device.name} 监控失败",
                        f"设备 {device.name} ({device.ip_address}) 监控失败: {str(e)}"
                    )
        finally:
            db.close()
    
    async def collect_device_metrics(self, device: Device):
        """收集设备指标"""
        try:
            metrics = await self.device_service.get_metrics(device)
            
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
                
                # 保存内存指标
                if 'memory' in metrics:
                    db.add(DeviceMetric(
                        device_id=device.id,
                        metric_type="memory",
                        metric_value=metrics['memory'],
                        unit="%"
                    ))
                
                # 保存接口指标（简化处理）
                if 'interfaces' in metrics:
                    # 这里可以解析接口流量信息
                    pass
                
                db.commit()
            finally:
                db.close()
            
            # 更新设备最后在线时间
            db = next(get_db())
            try:
                device.last_seen = datetime.utcnow()
                db.commit()
            finally:
                db.close()
                
        except Exception as e:
            print(f"收集设备 {device.name} 指标失败: {str(e)}")
            raise
    
    async def check_device_health(self, device: Device, db: Session):
        """检查设备健康状态"""
        try:
            health = await self.device_service.check_health(device)
            
            # 检查CPU使用率
            cpu_threshold = self.monitoring_config.get("cpu_threshold", 80)
            if 'cpu' in health and health['cpu'] > cpu_threshold:
                await self.create_alert(
                    db, device, "high_cpu", "warning",
                    f"设备 {device.name} CPU使用率过高",
                    f"设备 {device.name} CPU使用率达到 {health['cpu']}%，超过阈值 {cpu_threshold}%"
                )
            
            # 检查内存使用率
            memory_threshold = self.monitoring_config.get("memory_threshold", 85)
            if 'memory' in health and health['memory'] > memory_threshold:
                await self.create_alert(
                    db, device, "high_memory", "warning",
                    f"设备 {device.name} 内存使用率过高",
                    f"设备 {device.name} 内存使用率达到 {health['memory']}%，超过阈值 {memory_threshold}%"
                )
            
            # 检查健康问题
            if health.get("status") == "warning" and health.get("issues"):
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
            
        except Exception as e:
            print(f"检查设备 {device.name} 健康状态失败: {str(e)}")
    
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
        alert = Alert(
            device_id=device.id if device else None,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message
        )
        db.add(alert)
        db.commit()
        
        # 发送通知
        if self.notification_service and severity in ["critical", "warning"]:
            await self.notification_service.send_alert(alert_type, severity, title, message)

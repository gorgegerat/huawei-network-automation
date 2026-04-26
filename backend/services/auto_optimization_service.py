import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import Device, DeviceMetric, OptimizationLog, get_db
from services.huawei_device_service import HuaweiDeviceService
from services.notification_service import NotificationService

class AutoOptimizationService:
    """自动优化服务 - 根据网络状况自动优化配置"""
    
    def __init__(self, config: Dict[str, Any], notification_service: Optional[NotificationService]):
        self.config = config
        self.notification_service = notification_service
        self.scheduler = AsyncIOScheduler()
        self.device_service = HuaweiDeviceService()
        self.auto_config = config.get("auto_optimization", {})
    
    async def start(self):
        """启动自动优化服务"""
        if not self.auto_config.get("enabled", False):
            print("自动优化服务未启用")
            return
        
        check_interval = self.auto_config.get("check_interval", 300)
        
        # 添加定时任务
        self.scheduler.add_job(
            self.optimize_all_devices,
            'interval',
            seconds=check_interval,
            id='optimize_all_devices'
        )
        
        self.scheduler.start()
        print("自动优化服务已启动")
    
    async def stop(self):
        """停止自动优化服务"""
        self.scheduler.shutdown()
        print("自动优化服务已停止")
    
    async def optimize_all_devices(self):
        """优化所有设备"""
        db = next(get_db())
        try:
            devices = db.query(Device).filter(Device.status == "online").all()
            
            for device in devices:
                try:
                    await self.optimize_device(device)
                except Exception as e:
                    print(f"优化设备 {device.name} 失败: {str(e)}")
        finally:
            db.close()
    
    async def optimize_device(self, device: Device) -> Dict[str, Any]:
        """优化单个设备"""
        db = next(get_db())
        try:
            results = []
            
            # 路由优化
            if self.auto_config.get("enable_route_optimization", True):
                route_result = await self.optimize_route(device, db)
                results.append(route_result)
            
            # 带宽管理
            if self.auto_config.get("enable_bandwidth_management", True):
                bandwidth_result = await self.manage_bandwidth(device, db)
                results.append(bandwidth_result)
            
            # 负载均衡
            if self.auto_config.get("enable_load_balancing", True):
                lb_result = await self.configure_load_balancing(device, db)
                results.append(lb_result)
            
            return {
                "device_id": device.id,
                "device_name": device.name,
                "optimizations": results
            }
        finally:
            db.close()
    
    async def optimize_route(self, device: Device, db: Session) -> Dict[str, Any]:
        """优化路由配置"""
        try:
            # 获取最近的延迟指标
            recent_metrics = db.query(DeviceMetric).filter(
                DeviceMetric.device_id == device.id,
                DeviceMetric.metric_type == "latency",
                DeviceMetric.timestamp >= datetime.utcnow() - timedelta(minutes=10)
            ).all()
            
            if not recent_metrics:
                return {"type": "route", "status": "skipped", "reason": "无延迟数据"}
            
            # 计算平均延迟
            avg_latency = sum(m.metric_value for m in recent_metrics) / len(recent_metrics)
            
            monitoring_config = self.config.get("monitoring", {})
            latency_threshold = monitoring_config.get("latency_threshold", 100)
            
            if avg_latency > latency_threshold:
                # 延迟过高，触发路由优化
                old_config = await self.device_service.get_current_route_config(device)
                
                # 执行路由优化
                await self.device_service.optimize_route(device)
                
                new_config = await self.device_service.get_current_route_config(device)
                
                # 记录优化日志
                log = OptimizationLog(
                    device_id=device.id,
                    optimization_type="route_change",
                    old_config=old_config,
                    new_config=new_config,
                    reason=f"平均延迟 {avg_latency}ms 超过阈值 {latency_threshold}ms",
                    result="success"
                )
                db.add(log)
                db.commit()
                
                # 发送通知
                if self.notification_service:
                    await self.notification_service.send_alert(
                        "route_optimization",
                        "info",
                        f"设备 {device.name} 路由已优化",
                        f"由于延迟过高（{avg_latency}ms），已自动优化路由配置"
                    )
                
                return {"type": "route", "status": "optimized", "avg_latency": avg_latency}
            
            return {"type": "route", "status": "normal", "avg_latency": avg_latency}
            
        except Exception as e:
            print(f"路由优化失败: {str(e)}")
            return {"type": "route", "status": "failed", "error": str(e)}
    
    async def manage_bandwidth(self, device: Device, db: Session) -> Dict[str, Any]:
        """管理带宽"""
        try:
            # 获取最近的带宽指标
            recent_metrics = db.query(DeviceMetric).filter(
                DeviceMetric.device_id == device.id,
                DeviceMetric.metric_type == "bandwidth",
                DeviceMetric.timestamp >= datetime.utcnow() - timedelta(minutes=10)
            ).all()
            
            if not recent_metrics:
                return {"type": "bandwidth", "status": "skipped", "reason": "无带宽数据"}
            
            # 计算平均带宽使用率
            avg_bandwidth = sum(m.metric_value for m in recent_metrics) / len(recent_metrics)
            
            monitoring_config = self.config.get("monitoring", {})
            bandwidth_threshold = monitoring_config.get("bandwidth_threshold", 90)
            
            if avg_bandwidth > bandwidth_threshold:
                # 带宽使用率过高，触发带宽管理
                old_config = await self.device_service.get_current_qos_config(device)
                
                # 执行带宽管理（启用QoS）
                await self.device_service.enable_qos(device)
                
                new_config = await self.device_service.get_current_qos_config(device)
                
                # 记录优化日志
                log = OptimizationLog(
                    device_id=device.id,
                    optimization_type="bandwidth_adjustment",
                    old_config=old_config,
                    new_config=new_config,
                    reason=f"带宽使用率 {avg_bandwidth}% 超过阈值 {bandwidth_threshold}%",
                    result="success"
                )
                db.add(log)
                db.commit()
                
                return {"type": "bandwidth", "status": "managed", "avg_bandwidth": avg_bandwidth}
            
            return {"type": "bandwidth", "status": "normal", "avg_bandwidth": avg_bandwidth}
            
        except Exception as e:
            print(f"带宽管理失败: {str(e)}")
            return {"type": "bandwidth", "status": "failed", "error": str(e)}
    
    async def configure_load_balancing(self, device: Device, db: Session) -> Dict[str, Any]:
        """配置负载均衡"""
        try:
            # 检查是否有多条上行链路
            links = await self.device_service.get_uplink_links(device)
            
            if len(links) < 2:
                return {"type": "load_balance", "status": "skipped", "reason": "单链路无需负载均衡"}
            
            # 配置负载均衡
            old_config = await self.device_service.get_current_lb_config(device)
            
            await self.device_service.configure_load_balancing(device, links)
            
            new_config = await self.device_service.get_current_lb_config(device)
            
            # 记录优化日志
            log = OptimizationLog(
                device_id=device.id,
                optimization_type="load_balance",
                old_config=old_config,
                new_config=new_config,
                reason=f"检测到 {len(links)} 条上行链路，启用负载均衡",
                result="success"
            )
            db.add(log)
            db.commit()
            
            return {"type": "load_balance", "status": "enabled", "links": len(links)}
            
        except Exception as e:
            print(f"负载均衡配置失败: {str(e)}")
            return {"type": "load_balance", "status": "failed", "error": str(e)}

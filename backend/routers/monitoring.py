from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db, Device, DeviceMetric

router = APIRouter()

class MetricResponse(BaseModel):
    id: int
    device_id: int
    metric_type: str
    metric_value: float
    unit: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True

@router.get("/device/{device_id}", response_model=List[MetricResponse])
async def get_device_metrics(
    device_id: int,
    metric_type: Optional[str] = None,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    query = db.query(DeviceMetric).filter(DeviceMetric.device_id == device_id)
    
    if metric_type:
        query = query.filter(DeviceMetric.metric_type == metric_type)
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(DeviceMetric.timestamp >= start_time)
    
    metrics = query.order_by(DeviceMetric.timestamp.desc()).all()
    return metrics

@router.get("/device/{device_id}/latest")
async def get_latest_metrics(device_id: int, db: Session = Depends(get_db)):
    """获取设备最新指标"""
    metrics = {}
    metric_types = ["cpu", "memory", "bandwidth", "latency", "packet_loss"]
    
    for metric_type in metric_types:
        latest = db.query(DeviceMetric).filter(
            DeviceMetric.device_id == device_id,
            DeviceMetric.metric_type == metric_type
        ).order_by(DeviceMetric.timestamp.desc()).first()
        
        if latest:
            metrics[metric_type] = {
                "value": latest.metric_value,
                "unit": latest.unit,
                "timestamp": latest.timestamp
            }
    
    return metrics

@router.get("/device/{device_id}/summary")
async def get_device_summary(device_id: int, db: Session = Depends(get_db)):
    """获取设备状态摘要"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 获取最新指标
    latest_metrics = await get_latest_metrics(device_id, db)
    
    return {
        "device_id": device.id,
        "device_name": device.name,
        "device_type": device.device_type,
        "status": device.status,
        "last_seen": device.last_seen,
        "metrics": latest_metrics
    }

@router.post("/device/{device_id}/refresh")
async def refresh_metrics(device_id: int, db: Session = Depends(get_db)):
    """手动刷新设备指标"""
    from services.monitor_service import MonitorService
    import yaml
    from pathlib import Path
    
    config_path = Path("/app/config/config.yaml")
    if not config_path.exists():
        config_path = Path("../config/config.yaml")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    try:
        monitor = MonitorService(config, None)
        await monitor.collect_device_metrics(device)
        
        return {"message": "指标已刷新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新失败: {str(e)}")

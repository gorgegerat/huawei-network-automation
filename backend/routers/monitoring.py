from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta, timezone
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

    start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
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

@router.post("/force-stop")
async def force_stop_monitoring():
    """强制停止监控任务"""
    from main import monitor_service

    if not monitor_service:
        raise HTTPException(status_code=404, detail="监控服务未初始化")

    try:
        await monitor_service.force_stop()
        return {"message": "监控任务已强制停止"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"强制停止失败: {str(e)}")

@router.get("/status")
async def get_monitoring_status():
    """获取监控服务状态"""
    from main import monitor_service

    if not monitor_service:
        return {"running": False, "message": "监控服务未初始化"}

    try:
        status = monitor_service.get_current_task_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

@router.get("/export")
async def export_monitoring_results(
    device_id: Optional[int] = None,
    metric_type: Optional[str] = None,
    hours: int = 24,
    format: str = "excel",
    db: Session = Depends(get_db)
):
    """导出监控结果（支持Excel/CSV）"""
    try:
        import pandas as pd
        import io
        from fastapi.responses import Response, StreamingResponse

        # 构建查询
        query = db.query(DeviceMetric)

        if device_id:
            query = query.filter(DeviceMetric.device_id == device_id)

        if metric_type:
            query = query.filter(DeviceMetric.metric_type == metric_type)

        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = query.filter(DeviceMetric.timestamp >= start_time)

        metrics = query.order_by(DeviceMetric.timestamp.desc()).all()

        # 转换为DataFrame
        data = []
        for metric in metrics:
            device = db.query(Device).filter(Device.id == metric.device_id).first()
            data.append({
                '设备名称': device.name if device else '未知',
                '设备IP': device.ip_address if device else '未知',
                '指标类型': metric.metric_type,
                '指标值': metric.metric_value,
                '单位': metric.unit or '',
                '时间戳': metric.timestamp.isoformat() if metric.timestamp else ''
            })

        df = pd.DataFrame(data)

        # 根据格式输出
        if format == "csv":
            output = io.StringIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=monitoring_results.csv"}
            )
        else:  # excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='监控结果')
            output.seek(0)
            return StreamingResponse(
                io.BytesIO(output.getvalue()),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=monitoring_results.xlsx"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

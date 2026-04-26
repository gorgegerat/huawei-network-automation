from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import get_db, Device, OptimizationLog
from services.auto_optimization_service import AutoOptimizationService
import yaml
from pathlib import Path

router = APIRouter()

class OptimizationResponse(BaseModel):
    id: int
    device_id: Optional[int]
    optimization_type: str
    old_config: Optional[str]
    new_config: Optional[str]
    reason: Optional[str]
    result: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True

@router.get("/logs", response_model=List[OptimizationResponse])
async def get_optimization_logs(
    device_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(OptimizationLog)
    
    if device_id:
        query = query.filter(OptimizationLog.device_id == device_id)
    
    logs = query.order_by(OptimizationLog.created_at.desc()).limit(limit).all()
    return logs

@router.post("/trigger/{device_id}")
async def trigger_optimization(device_id: int, db: Session = Depends(get_db)):
    """手动触发设备优化"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    try:
        config_path = Path("/app/config/config.yaml")
        if not config_path.exists():
            config_path = Path("../config/config.yaml")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        service = AutoOptimizationService(config, None)
        result = await service.optimize_device(device)
        
        return {"message": "优化已完成", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"优化失败: {str(e)}")

@router.post("/route/optimize/{device_id}")
async def optimize_route(device_id: int, db: Session = Depends(get_db)):
    """优化路由配置"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    try:
        from services.huawei_device_service import HuaweiDeviceService
        service = HuaweiDeviceService()
        result = await service.optimize_route(device)
        
        return {"message": "路由优化完成", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"路由优化失败: {str(e)}")

@router.get("/status")
async def get_optimization_status():
    """获取自动优化状态"""
    config_path = Path("/app/config/config.yaml")
    if not config_path.exists():
        config_path = Path("../config/config.yaml")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    auto_config = config.get("auto_optimization", {})
    
    return {
        "enabled": auto_config.get("enabled", False),
        "check_interval": auto_config.get("check_interval", 300),
        "route_optimization": auto_config.get("enable_route_optimization", False),
        "bandwidth_management": auto_config.get("enable_bandwidth_management", False),
        "load_balancing": auto_config.get("enable_load_balancing", False)
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import get_db, Device, DeviceConfig
from services.huawei_device_service import HuaweiDeviceService

router = APIRouter()

class ConfigCreate(BaseModel):
    device_id: int
    config_name: str
    config_content: str
    version: Optional[str] = None

class ConfigResponse(BaseModel):
    id: int
    device_id: int
    config_name: str
    config_content: str
    version: Optional[str]
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True

@router.get("/device/{device_id}", response_model=List[ConfigResponse])
async def get_device_configs(device_id: int, db: Session = Depends(get_db)):
    configs = db.query(DeviceConfig).filter(DeviceConfig.device_id == device_id).all()
    return configs

@router.get("/{config_id}", response_model=ConfigResponse)
async def get_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(DeviceConfig).filter(DeviceConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config

@router.post("/", response_model=ConfigResponse)
async def create_config(config: ConfigCreate, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == config.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    new_config = DeviceConfig(**config.dict())
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    
    return new_config

@router.post("/{config_id}/activate")
async def activate_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(DeviceConfig).filter(DeviceConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    device = db.query(Device).filter(Device.id == config.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    try:
        service = HuaweiDeviceService()
        result = await service.apply_config(device, config.config_content)
        
        # 取消其他激活配置
        db.query(DeviceConfig).filter(
            DeviceConfig.device_id == config.device_id,
            DeviceConfig.is_active == True
        ).update({"is_active": False})
        
        # 激活当前配置
        config.is_active = True
        db.commit()
        
        return {"message": "配置已应用", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"应用配置失败: {str(e)}")

@router.post("/{config_id}/deploy")
async def deploy_config(config_id: int, db: Session = Depends(get_db)):
    """将配置部署到设备（新设备自动部署）"""
    config = db.query(DeviceConfig).filter(DeviceConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    device = db.query(Device).filter(Device.id == config.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    try:
        service = HuaweiDeviceService()
        result = await service.deploy_config(device, config.config_content)
        
        device.status = "online"
        device.last_seen = datetime.utcnow()
        db.commit()
        
        return {"message": "配置部署成功", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"部署失败: {str(e)}")

@router.delete("/{config_id}")
async def delete_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(DeviceConfig).filter(DeviceConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    db.delete(config)
    db.commit()
    
    return {"message": "配置已删除"}

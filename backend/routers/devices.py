from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from database import get_db, Device, DeviceConfig
from services.huawei_device_service import HuaweiDeviceService

router = APIRouter()

class DeviceCreate(BaseModel):
    name: str
    ip_address: str
    device_type: str  # switch, router, firewall
    model: Optional[str] = None
    serial_number: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_port: int = 22

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    device_type: Optional[str] = None
    model: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_port: Optional[int] = None

class DeviceResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    device_type: str
    model: Optional[str]
    serial_number: Optional[str]
    status: str
    last_seen: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[DeviceResponse])
async def get_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    return devices

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device

@router.post("/", response_model=DeviceResponse)
async def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    # 检查IP是否已存在
    existing = db.query(Device).filter(Device.ip_address == device.ip_address).first()
    if existing:
        raise HTTPException(status_code=400, detail="该IP地址的设备已存在")
    
    # 创建设备
    new_device = Device(**device.dict())
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    
    return new_device

@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: int, device: DeviceUpdate, db: Session = Depends(get_db)):
    db_device = db.query(Device).filter(Device.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    update_data = device.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_device, key, value)
    
    db_device.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_device)
    
    return db_device

@router.delete("/{device_id}")
async def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    db.delete(device)
    db.commit()
    
    return {"message": "设备已删除"}

@router.post("/{device_id}/connect")
async def connect_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    try:
        service = HuaweiDeviceService()
        result = await service.connect(device)
        
        device.status = "online"
        device.last_seen = datetime.utcnow()
        db.commit()
        
        return {"message": "连接成功", "device_info": result}
    except Exception as e:
        device.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")

@router.post("/{device_id}/disconnect")
async def disconnect_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    device.status = "offline"
    db.commit()
    
    return {"message": "设备已断开连接"}

@router.post("/{device_id}/discover")
async def discover_device(device_id: int, db: Session = Depends(get_db)):
    """自动发现设备信息"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    try:
        service = HuaweiDeviceService()
        info = await service.discover_device(device)
        
        # 更新设备信息
        if info.get("model"):
            device.model = info["model"]
        if info.get("serial_number"):
            device.serial_number = info["serial_number"]
        
        db.commit()
        
        return {"message": "设备信息已更新", "info": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发现失败: {str(e)}")

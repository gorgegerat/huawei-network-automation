from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import pandas as pd
import io
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
    group: str = "未分组"

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    device_type: Optional[str] = None
    model: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_port: Optional[int] = None
    group: Optional[str] = None

class DeviceResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    device_type: str
    model: Optional[str]
    serial_number: Optional[str]
    status: str
    last_seen: Optional[datetime]
    group: str
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

@router.get("/groups/list")
async def get_groups(db: Session = Depends(get_db)):
    """获取所有设备分组"""
    groups = db.query(Device.group).distinct().all()
    return {"groups": [group[0] for group in groups if group[0]]}

@router.get("/group/{group_name}", response_model=List[DeviceResponse])
async def get_devices_by_group(group_name: str, db: Session = Depends(get_db)):
    """获取指定分组的设备"""
    devices = db.query(Device).filter(Device.group == group_name).all()
    return devices

@router.put("/{device_id}/group")
async def update_device_group(device_id: int, group: str, db: Session = Depends(get_db)):
    """更新设备分组"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    device.group = group
    device.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "设备分组已更新", "group": group}

@router.post("/import")
async def import_devices(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """批量导入设备（支持Excel/CSV）"""
    try:
        # 读取文件内容
        content = await file.read()
        
        # 根据文件类型解析
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式，请使用CSV或Excel")
        
        # 验证必需列
        required_columns = ['name', 'ip_address', 'device_type']
        for col in required_columns:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"缺少必需列: {col}")
        
        # 批量创建设备
        success_count = 0
        failed_count = 0
        errors = []
        
        for _, row in df.iterrows():
            try:
                # 检查IP是否已存在
                existing = db.query(Device).filter(Device.ip_address == str(row['ip_address'])).first()
                if existing:
                    failed_count += 1
                    errors.append(f"IP {row['ip_address']} 已存在")
                    continue
                
                # 创建设备
                device = Device(
                    name=str(row['name']),
                    ip_address=str(row['ip_address']),
                    device_type=str(row['device_type']),
                    model=str(row.get('model', '')) if pd.notna(row.get('model')) else None,
                    serial_number=str(row.get('serial_number', '')) if pd.notna(row.get('serial_number')) else None,
                    username=str(row.get('username', '')) if pd.notna(row.get('username')) else None,
                    password=str(row.get('password', '')) if pd.notna(row.get('password')) else None,
                    ssh_port=int(row.get('ssh_port', 22)) if pd.notna(row.get('ssh_port')) else 22,
                    group=str(row.get('group', '未分组')) if pd.notna(row.get('group')) else '未分组'
                )
                db.add(device)
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"行 {_}: {str(e)}")
        
        db.commit()
        
        return {
            "message": "导入完成",
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

@router.get("/export")
async def export_devices(format: str = "excel", db: Session = Depends(get_db)):
    """批量导出设备（支持Excel/CSV）"""
    try:
        devices = db.query(Device).all()
        
        # 转换为DataFrame
        data = []
        for device in devices:
            data.append({
                'name': device.name,
                'ip_address': device.ip_address,
                'device_type': device.device_type,
                'model': device.model or '',
                'serial_number': device.serial_number or '',
                'username': device.username or '',
                'ssh_port': device.ssh_port,
                'group': device.group or '未分组',
                'status': device.status,
                'last_seen': device.last_seen.isoformat() if device.last_seen else '',
                'created_at': device.created_at.isoformat() if device.created_at else ''
            })
        
        df = pd.DataFrame(data)
        
        # 根据格式输出
        if format == "csv":
            output = io.StringIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')
            from fastapi.responses import Response
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=devices.csv"}
            )
        else:  # excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='设备列表')
            output.seek(0)
            from fastapi.responses import StreamingResponse
            return StreamingResponse(
                io.BytesIO(output.getvalue()),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=devices.xlsx"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

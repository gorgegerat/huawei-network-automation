"""
ZTP零接触部署API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ztp", tags=["ZTP"])


# 模型定义
class TemplateCreate(BaseModel):
    template_id: str
    name: str
    device_type: str
    content: str
    variables: Optional[List[str]] = None


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[List[str]] = None


class DeviceAssignment(BaseModel):
    mac_address: str
    template_id: str
    variables: Optional[Dict[str, Any]] = None


class ConfigRequest(BaseModel):
    mac_address: str
    variables: Optional[Dict[str, Any]] = None


# ZTP服务实例（实际应该从依赖注入获取）
ztp_service = None


def set_ztp_service(service):
    """设置ZTP服务实例"""
    global ztp_service
    ztp_service = service


@router.get("/status")
async def get_ztp_status():
    """获取ZTP服务状态"""
    if not ztp_service:
        return {"enabled": False, "message": "ZTP服务未启动"}
    
    return ztp_service.get_status()


@router.get("/templates")
async def list_templates():
    """列出所有配置模板"""
    if not ztp_service:
        raise HTTPException(status_code=503, detail="ZTP服务未启动")
    
    templates = ztp_service.config_service.list_templates()
    return {"templates": templates}


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """获取配置模板详情"""
    if not ztp_service:
        raise HTTPException(status_code=503, detail="ZTP服务未启动")
    
    template = ztp_service.config_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return template


@router.post("/templates")
async def create_template(template: TemplateCreate):
    """创建配置模板"""
    if not ztp_service:
        raise HTTPException(status_code=503, detail="ZTP服务未启动")
    
    try:
        new_template = ztp_service.config_service.create_template(
            template_id=template.template_id,
            name=template.name,
            device_type=template.device_type,
            content=template.content,
            variables=template.variables
        )
        return new_template.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/templates/{template_id}")
async def update_template(template_id: str, template: TemplateUpdate):
    """更新配置模板"""
    if not ztp_service:
        raise HTTPException(status_code=503, detail="ZTP服务未启动")
    
    try:
        update_data = {k: v for k, v in template.dict().items() if v is not None}
        updated_template = ztp_service.config_service.update_template(template_id, **update_data)
        return updated_template.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """删除配置模板"""
    if not ztp_service:
        raise HTTPException(status_code=503, detail="ZTP服务未启动")
    
    try:
        ztp_service.config_service.delete_template(template_id)
        return {"message": "模板删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/devices/assign")
async def assign_template_to_device(assignment: DeviceAssignment):
    """为设备分配配置模板"""
    if not ztp_service:
        raise HTTPException(status_code=503, detail="ZTP服务未启动")
    
    try:
        ztp_service.config_service.assign_template_to_device(
            assignment.mac_address,
            assignment.template_id
        )
        return {"message": "模板分配成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/devices/config")
async def get_device_config(request: ConfigRequest):
    """获取设备配置（用于ZTP）"""
    if not ztp_service:
        raise HTTPException(status_code=503, detail="ZTP服务未启动")
    
    variables = request.variables or {}
    config = ztp_service.config_service.get_config_for_device(
        request.mac_address,
        **variables
    )
    
    if not config:
        raise HTTPException(status_code=404, detail="无法生成配置")
    
    return {"config": config}


@router.get("/devices/discovered")
async def get_discovered_devices():
    """获取发现的设备列表"""
    if not ztp_service:
        raise HTTPException(status_code=503, detail="ZTP服务未启动")
    
    devices = ztp_service.device_discovery.get_discovered_devices()
    return {"devices": devices}


@router.get("/devices/discovered/{mac_address}")
async def get_discovered_device(mac_address: str):
    """获取发现的设备详情"""
    if not ztp_service:
        raise HTTPException(status_code=503, detail="ZTP服务未启动")
    
    device = ztp_service.device_discovery.get_device(mac_address)
    if not device:
        raise HTTPException(status_code=404, detail="设备未发现")
    
    return device


@router.post("/devices/discovery/start")
async def start_device_discovery():
    """启动设备发现"""
    if not ztp_service:
        raise HTTPException(status_code=503, detail="ZTP服务未启动")
    
    ztp_service.device_discovery.start()
    return {"message": "设备发现已启动"}


@router.post("/devices/discovery/stop")
async def stop_device_discovery():
    """停止设备发现"""
    if not ztp_service:
        raise HTTPException(status_code=503, detail="ZTP服务未启动")
    
    ztp_service.device_discovery.stop()
    return {"message": "设备发现已停止"}


@router.post("/devices/discovery/clear")
async def clear_old_devices(max_age_hours: int = 24):
    """清除旧的设备记录"""
    if not ztp_service:
        raise HTTPException(status_code=503, detail="ZTP服务未启动")
    
    ztp_service.device_discovery.clear_old_devices(max_age_hours)
    return {"message": "旧设备记录已清除"}

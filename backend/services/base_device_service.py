from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from database import Device


class BaseDeviceService(ABC):
    """设备服务基类 - 抽象接口"""
    
    def __init__(self):
        self.connections = {}
    
    @abstractmethod
    async def connect(self, device: Device) -> Dict[str, Any]:
        """连接到设备"""
        pass
    
    @abstractmethod
    async def disconnect(self, device_id: int) -> bool:
        """断开设备连接"""
        pass
    
    @abstractmethod
    async def get_device_info(self, device: Device) -> Dict[str, Any]:
        """获取设备信息"""
        pass
    
    @abstractmethod
    async def execute_command(self, device: Device, command: str) -> str:
        """执行命令"""
        pass
    
    @abstractmethod
    async def get_config(self, device: Device) -> str:
        """获取设备配置"""
        pass
    
    @abstractmethod
    async def save_config(self, device: Device) -> bool:
        """保存设备配置"""
        pass
    
    @abstractmethod
    async def get_metrics(self, device: Device) -> Dict[str, Any]:
        """获取设备指标"""
        pass
    
    @abstractmethod
    def get_supported_commands(self) -> List[str]:
        """获取支持的命令列表"""
        pass
    
    @abstractmethod
    def parse_device_type(self, device_info: str) -> str:
        """解析设备类型"""
        pass

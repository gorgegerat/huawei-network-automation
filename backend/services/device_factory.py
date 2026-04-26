from typing import Dict, Type
from services.base_device_service import BaseDeviceService
from services.huawei_device_service import HuaweiDeviceService


class DeviceFactory:
    """设备工厂 - 根据厂商创建对应的服务实例"""
    
    _services: Dict[str, Type[BaseDeviceService]] = {
        'huawei': HuaweiDeviceService,
        # 未来可以添加更多厂商
        # 'cisco': CiscoDeviceService,
        # 'h3c': H3CDeviceService,
        # 'ruijie': RuijieDeviceService,
    }
    
    @classmethod
    def register_service(cls, vendor: str, service_class: Type[BaseDeviceService]):
        """注册新的设备服务"""
        cls._services[vendor.lower()] = service_class
    
    @classmethod
    def create_service(cls, vendor: str) -> BaseDeviceService:
        """根据厂商创建设备服务实例"""
        vendor = vendor.lower()
        if vendor not in cls._services:
            raise ValueError(f"不支持的设备厂商: {vendor}")
        
        return cls._services[vendor]()
    
    @classmethod
    def get_supported_vendors(cls) -> list:
        """获取支持的厂商列表"""
        return list(cls._services.keys())
    
    @classmethod
    def is_supported(cls, vendor: str) -> bool:
        """检查厂商是否支持"""
        return vendor.lower() in cls._services

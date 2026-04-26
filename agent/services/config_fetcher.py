import httpx
from typing import Dict, Any, Optional
import yaml
from pathlib import Path

class ConfigFetcher:
    """配置获取服务 - 从云端API获取配置"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_base_url = config.get("agent", {}).get("api_base_url", "http://backend:8000")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def check_device_registered(self, ip: str) -> bool:
        """检查设备是否已注册"""
        try:
            response = await self.client.get(f"{self.api_base_url}/api/devices/ip/{ip}")
            return response.status_code == 200
        except Exception as e:
            print(f"检查设备注册状态失败: {str(e)}")
            return False
    
    async def register_device(self, device: Dict[str, Any], deploy_result: Dict[str, Any]) -> bool:
        """注册设备到云端"""
        try:
            device_data = {
                "name": f"Huawei-{device['ip']}",
                "ip_address": device['ip'],
                "device_type": "switch",  # 根据实际情况判断
                "model": device.get('model'),
                "serial_number": device.get('serial_number'),
                "username": self.config.get("huawei", {}).get("default_username"),
                "password": self.config.get("huawei", {}).get("default_password"),
                "ssh_port": 22
            }
            
            response = await self.client.post(f"{self.api_base_url}/api/devices", json=device_data)
            return response.status_code == 200
        except Exception as e:
            print(f"注册设备失败: {str(e)}")
            return False
    
    async def get_registered_devices(self) -> list:
        """获取所有已注册设备"""
        try:
            response = await self.client.get(f"{self.api_base_url}/api/devices")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"获取已注册设备失败: {str(e)}")
            return []
    
    async def fetch_config_for_device(self, device: Dict[str, Any]) -> Optional[str]:
        """为设备获取配置"""
        try:
            # 根据设备类型和型号获取配置模板
            device_type = device.get('device_type', 'switch')
            model = device.get('model', 'default')
            
            # 从云端获取配置模板
            response = await self.client.get(
                f"{self.api_base_url}/api/configs/template/{device_type}/{model}"
            )
            
            if response.status_code == 200:
                config_data = response.json()
                return config_data.get('config_content')
            
            # 如果没有特定配置，使用默认配置
            return self.get_default_config(device)
        
        except Exception as e:
            print(f"获取配置失败: {str(e)}")
            return self.get_default_config(device)
    
    def get_default_config(self, device: Dict[str, Any]) -> str:
        """获取默认配置"""
        # 根据设备类型生成默认配置
        config = f"""
# 华为设备默认配置
# 设备IP: {device['ip']}
# 型号: {device.get('model', 'Unknown')}

sysname Huawei-{device['ip'].replace('.', '-')}

# 管理接口配置
interface Vlanif1
 ip address {device['ip']} 255.255.255.0

# SSH配置
stelnet server enable
ssh user {self.config.get('huawei', {}).get('default_username', 'admin')}
 ssh-user authentication-type password

# SNMP配置
snmp-agent
snmp-agent sys-info version all
snmp-agent target-host trap address udp-domain 127.0.0.1 params securityname public

# 启用所有接口
interface GigabitEthernet0/0/1
 undo shutdown
"""
        return config
    
    async def check_config_update(self, device: Dict[str, Any]) -> bool:
        """检查配置是否需要更新"""
        try:
            response = await self.client.get(
                f"{self.api_base_url}/api/configs/device/{device['id']}/check-update"
            )
            if response.status_code == 200:
                return response.json().get('needs_update', False)
            return False
        except Exception as e:
            print(f"检查配置更新失败: {str(e)}")
            return False

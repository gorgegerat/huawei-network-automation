import asyncio
import subprocess
import re
from typing import List, Dict, Any
from netmiko import ConnectHandler
from netmiko.huawei import HuaweiSSH

class DeviceDiscovery:
    """设备发现服务"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.huawei_config = config.get("huawei", {})
    
    async def scan_network(self) -> List[Dict[str, Any]]:
        """扫描网络中的华为设备"""
        devices = []
        
        # 获取网络范围
        network_ranges = self.config.get("agent", {}).get("network_ranges", ["192.168.1.0/24"])
        
        for network in network_ranges:
            print(f"扫描网络: {network}")
            network_devices = await self.scan_network_range(network)
            devices.extend(network_devices)
        
        return devices
    
    async def scan_network_range(self, network: str) -> List[Dict[str, Any]]:
        """扫描指定网络范围"""
        devices = []
        
        try:
            # 使用nmap扫描（如果可用）
            result = subprocess.run(
                ["nmap", "-p", "22", "--open", network],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                # 解析nmap输出
                ip_pattern = r'Nmap scan report for ([\d.]+)'
                ips = re.findall(ip_pattern, result.stdout)
                
                for ip in ips:
                    # 尝试连接并识别华为设备
                    device_info = await self.identify_huawei_device(ip)
                    if device_info:
                        devices.append(device_info)
        
        except FileNotFoundError:
            # nmap不可用，使用ping扫描
            print("nmap不可用，使用ping扫描")
            devices = await self.ping_scan(network)
        
        except Exception as e:
            print(f"扫描网络失败: {str(e)}")
        
        return devices
    
    async def ping_scan(self, network: str) -> List[Dict[str, Any]]:
        """使用ping扫描网络"""
        devices = []
        
        # 简化处理：扫描常见IP段
        base_ip = network.split('/')[0].rsplit('.', 1)[0]
        
        for i in range(1, 255):
            ip = f"{base_ip}.{i}"
            
            try:
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", "1", ip],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.returncode == 0:
                    # 检查是否是华为设备
                    device_info = await self.identify_huawei_device(ip)
                    if device_info:
                        devices.append(device_info)
            
            except Exception:
                continue
        
        return devices
    
    async def identify_huawei_device(self, ip: str) -> Dict[str, Any]:
        """识别华为设备"""
        try:
            device_info = {
                'device_type': 'huawei',
                'host': ip,
                'username': self.huawei_config.get('default_username', 'admin'),
                'password': self.huawei_config.get('default_password', 'Admin@123'),
                'port': self.huawei_config.get('ssh_port', 22),
                'timeout': 10,
            }
            
            connection = ConnectHandler(**device_info)
            
            # 获取版本信息
            version_output = connection.send_command('display version')
            
            # 检查是否是华为设备
            if 'Huawei' in version_output or 'HUAWEI' in version_output:
                # 提取设备信息
                model_match = re.search(r'Huawei\s+(\S+)', version_output)
                serial_match = re.search(r'ESN\s*:\s*(\S+)', version_output)
                
                device_info = {
                    'ip': ip,
                    'manufacturer': 'Huawei',
                    'model': model_match.group(1) if model_match else 'Unknown',
                    'serial_number': serial_match.group(1) if serial_match else None,
                    'version': version_output
                }
                
                connection.disconnect()
                return device_info
            
            connection.disconnect()
            return None
        
        except Exception as e:
            # 连接失败，可能不是华为设备或凭据错误
            return None

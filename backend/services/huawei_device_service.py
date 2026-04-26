import asyncio
from netmiko import ConnectHandler
from typing import Dict, Any, Optional, List
import re
from database import Device, DeviceConfig
from services.base_device_service import BaseDeviceService

class HuaweiDeviceService(BaseDeviceService):
    """华为设备交互服务"""
    
    def __init__(self):
        super().__init__()
        self.vendor = "huawei"
    
    async def connect(self, device: Device) -> Dict[str, Any]:
        """连接到华为设备"""
        try:
            device_info = {
                'device_type': 'huawei',
                'host': device.ip_address,
                'username': device.username or 'admin',
                'password': device.password,
                'port': device.ssh_port or 22,
                'timeout': 30,
                'session_timeout': 60,
            }
            
            connection = ConnectHandler(**device_info)
            self.connections[device.id] = connection
            
            # 获取设备信息
            output = connection.send_command('display version')
            
            return {
                "status": "connected",
                "version_output": output
            }
        except Exception as e:
            raise Exception(f"连接失败: {str(e)}")
    
    async def disconnect(self, device_id: int) -> bool:
        """断开设备连接"""
        if device_id in self.connections:
            self.connections[device_id].disconnect()
            del self.connections[device_id]
            return True
        return False
    
    async def get_device_info(self, device: Device) -> Dict[str, Any]:
        """获取设备信息"""
        return await self.discover_device(device)
    
    async def discover_device(self, device: Device) -> Dict[str, Any]:
        """自动发现设备信息"""
        if device.id not in self.connections:
            await self.connect(device)
        
        connection = self.connections[device.id]
        
        info = {}
        
        # 获取版本信息
        version_output = connection.send_command('display version')
        info['version'] = version_output
        
        # 提取型号
        model_match = re.search(r'Huawei\s+(\S+)', version_output)
        if model_match:
            info['model'] = model_match.group(1)
        
        # 提取序列号
        serial_match = re.search(r'ESN\s*:\s*(\S+)', version_output)
        if serial_match:
            info['serial_number'] = serial_match.group(1)
        
        # 获取接口信息
        interface_output = connection.send_command('display interface')
        info['interfaces'] = interface_output
        
        # 获取配置
        config_output = connection.send_command('display current-configuration')
        info['current_config'] = config_output
        
        return info
    
    async def apply_config(self, device: Device, config_content: str) -> Dict[str, Any]:
        """应用配置到设备"""
        if device.id not in self.connections:
            await self.connect(device)
        
        connection = self.connections[device.id]
        
        try:
            # 进入系统视图
            connection.send_command('system-view')
            
            # 分割配置命令并逐条执行
            commands = [line.strip() for line in config_content.split('\n') if line.strip()]
            
            results = []
            for cmd in commands:
                if cmd and not cmd.startswith('!'):
                    output = connection.send_command(cmd, expect_string=r']|#|\$')
                    results.append({
                        "command": cmd,
                        "output": output
                    })
            
            # 保存配置
            connection.send_command('return')
            connection.send_command('save')
            connection.send_command('y')  # 确认保存
            
            return {
                "status": "success",
                "commands_executed": len(results),
                "results": results
            }
        except Exception as e:
            raise Exception(f"应用配置失败: {str(e)}")
    
    async def deploy_config(self, device: Device, config_content: str) -> Dict[str, Any]:
        """部署配置到新设备（自动部署）"""
        if device.id not in self.connections:
            await self.connect(device)
        
        connection = self.connections[device.id]
        
        try:
            # 清空现有配置
            connection.send_command('reset saved-configuration')
            connection.send_command('y')
            connection.send_command('reboot')
            connection.send_command('y')
            
            # 等待设备重启
            await asyncio.sleep(60)
            
            # 重新连接
            await self.connect(device)
            
            # 应用新配置
            result = await self.apply_config(device, config_content)
            
            return {
                "status": "deployed",
                "result": result
            }
        except Exception as e:
            raise Exception(f"部署失败: {str(e)}")
    
    async def get_metrics(self, device: Device) -> Dict[str, Any]:
        """获取设备性能指标"""
        if device.id not in self.connections:
            await self.connect(device)
        
        connection = self.connections[device.id]
        
        metrics = {}
        
        # CPU使用率
        cpu_output = connection.send_command('display cpu-usage')
        cpu_match = re.search(r'(\d+)%', cpu_output)
        if cpu_match:
            metrics['cpu'] = float(cpu_match.group(1))
        
        # 内存使用率
        memory_output = connection.send_command('display memory-usage')
        memory_match = re.search(r'(\d+)%', memory_output)
        if memory_match:
            metrics['memory'] = float(memory_match.group(1))
        
        # 接口流量
        interface_output = connection.send_command('display interface')
        metrics['interfaces'] = interface_output
        
        # 路由表
        route_output = connection.send_command('display ip routing-table')
        metrics['routes'] = route_output
        
        return metrics
    
    async def optimize_route(self, device: Device) -> Dict[str, Any]:
        """优化路由配置"""
        if device.id not in self.connections:
            await self.connect(device)
        
        connection = self.connections[device.id]
        
        try:
            # 获取当前路由表
            route_output = connection.send_command('display ip routing-table')
            
            # 分析路由并生成优化建议
            # 这里简化处理，实际需要根据网络拓扑进行智能分析
            
            connection.send_command('system-view')
            
            # 启用OSPF（示例）
            connection.send_command('ospf 1')
            connection.send_command('area 0')
            connection.send_command('network 0.0.0.0 0.0.0.0')
            connection.send_command('return')
            
            # 保存配置
            connection.send_command('save')
            connection.send_command('y')
            
            return {
                "status": "optimized",
                "message": "路由优化已完成"
            }
        except Exception as e:
            raise Exception(f"路由优化失败: {str(e)}")
    
    async def check_health(self, device: Device) -> Dict[str, Any]:
        """检查设备健康状态"""
        if device.id not in self.connections:
            await self.connect(device)
        
        connection = self.connections[device.id]
        
        health = {
            "status": "healthy",
            "issues": []
        }
        
        try:
            # 检查CPU
            cpu_output = connection.send_command('display cpu-usage')
            cpu_match = re.search(r'(\d+)%', cpu_output)
            if cpu_match:
                cpu_usage = float(cpu_match.group(1))
                if cpu_usage > 90:
                    health["status"] = "warning"
                    health["issues"].append(f"CPU使用率过高: {cpu_usage}%")
            
            # 检查内存
            memory_output = connection.send_command('display memory-usage')
            memory_match = re.search(r'(\d+)%', memory_output)
            if memory_match:
                memory_usage = float(memory_match.group(1))
                if memory_usage > 90:
                    health["status"] = "warning"
                    health["issues"].append(f"内存使用率过高: {memory_usage}%")
            
            # 检查接口状态
            interface_output = connection.send_command('display interface brief')
            if 'down' in interface_output.lower():
                health["status"] = "warning"
                health["issues"].append("存在接口down状态")
            
            return health
        except Exception as e:
            health["status"] = "error"
            health["issues"].append(f"健康检查失败: {str(e)}")
            return health
    
    async def execute_command(self, device: Device, command: str) -> str:
        """执行命令"""
        if device.id not in self.connections:
            await self.connect(device)
        
        connection = self.connections[device.id]
        return connection.send_command(command)
    
    async def get_config(self, device: Device) -> str:
        """获取设备配置"""
        if device.id not in self.connections:
            await self.connect(device)
        
        connection = self.connections[device.id]
        return connection.send_command('display current-configuration')
    
    async def save_config(self, device: Device) -> bool:
        """保存设备配置"""
        if device.id not in self.connections:
            await self.connect(device)
        
        connection = self.connections[device.id]
        try:
            connection.send_command('save')
            connection.send_command('y')
            return True
        except Exception:
            return False
    
    def get_supported_commands(self) -> List[str]:
        """获取支持的命令列表"""
        return [
            'display version',
            'display interface',
            'display current-configuration',
            'display cpu-usage',
            'display memory-usage',
            'display ip routing-table',
            'system-view',
            'save'
        ]
    
    def parse_device_type(self, device_info: str) -> str:
        """解析设备类型"""
        if 'switch' in device_info.lower() or 's' in device_info.lower():
            return 'switch'
        elif 'router' in device_info.lower() or 'ar' in device_info.lower():
            return 'router'
        elif 'firewall' in device_info.lower() or 'usg' in device_info.lower():
            return 'firewall'
        return 'unknown'

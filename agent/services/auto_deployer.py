from netmiko import ConnectHandler
from netmiko.huawei import HuaweiSSH
from typing import Dict, Any, Optional
import re

class AutoDeployer:
    """自动部署服务"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.huawei_config = config.get("huawei", {})
    
    async def deploy(self, device: Dict[str, Any], config_content: str) -> Dict[str, Any]:
        """自动部署配置到新设备"""
        try:
            print(f"开始部署设备 {device['ip']}...")
            
            # 连接设备
            connection = await self.connect_device(device)
            
            if not connection:
                return {"success": False, "error": "连接设备失败"}
            
            try:
                # 清空现有配置
                print("清空现有配置...")
                connection.send_command('reset saved-configuration')
                connection.send_command('y')
                
                # 重启设备
                print("重启设备...")
                connection.send_command('reboot')
                connection.send_command('y')
                
                connection.disconnect()
                
                # 等待设备重启
                print("等待设备重启...")
                await asyncio.sleep(60)
                
                # 重新连接
                print("重新连接设备...")
                connection = await self.connect_device(device)
                
                if not connection:
                    return {"success": False, "error": "重启后连接失败"}
                
                # 应用新配置
                print("应用新配置...")
                result = await self.apply_config_commands(connection, config_content)
                
                # 保存配置
                print("保存配置...")
                connection.send_command('save')
                connection.send_command('y')
                
                connection.disconnect()
                
                return {
                    "success": True,
                    "message": "配置部署成功",
                    "details": result
                }
            
            except Exception as e:
                connection.disconnect()
                raise e
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def apply_config(self, device: Dict[str, Any], config_content: str) -> Dict[str, Any]:
        """应用配置到已运行的设备"""
        try:
            connection = await self.connect_device(device)
            
            if not connection:
                return {"success": False, "error": "连接设备失败"}
            
            try:
                result = await self.apply_config_commands(connection, config_content)
                
                # 保存配置
                connection.send_command('save')
                connection.send_command('y')
                
                connection.disconnect()
                
                return {
                    "success": True,
                    "message": "配置应用成功",
                    "details": result
                }
            
            except Exception as e:
                connection.disconnect()
                raise e
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def connect_device(self, device: Dict[str, Any]) -> Optional[ConnectHandler]:
        """连接到设备"""
        try:
            device_info = {
                'device_type': 'huawei',
                'host': device['ip'],
                'username': self.huawei_config.get('default_username', 'admin'),
                'password': self.huawei_config.get('default_password', 'Admin@123'),
                'port': self.huawei_config.get('ssh_port', 22),
                'timeout': 30,
            }
            
            connection = ConnectHandler(**device_info)
            return connection
        
        except Exception as e:
            print(f"连接设备失败: {str(e)}")
            return None
    
    async def apply_config_commands(self, connection: ConnectHandler, config_content: str) -> Dict[str, Any]:
        """应用配置命令"""
        commands = [line.strip() for line in config_content.split('\n') if line.strip() and not line.startswith('#')]
        
        results = []
        current_view = None
        
        for cmd in commands:
            try:
                # 处理视图切换
                if 'system-view' in cmd:
                    connection.send_command('system-view')
                    current_view = 'system'
                    continue
                
                if 'return' in cmd:
                    connection.send_command('return')
                    current_view = None
                    continue
                
                # 执行命令
                output = connection.send_command(cmd, expect_string=r']|#|\$')
                results.append({
                    "command": cmd,
                    "output": output,
                    "success": True
                })
            
            except Exception as e:
                results.append({
                    "command": cmd,
                    "error": str(e),
                    "success": False
                })
        
        return {
            "total_commands": len(commands),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "results": results
        }

import asyncio

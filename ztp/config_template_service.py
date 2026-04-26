#!/usr/bin/env python3
"""
ZTP配置模板服务
管理配置模板和设备配置生成
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import yaml
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigTemplate:
    """配置模板"""

    def __init__(self, template_id: str, name: str, device_type: str,
                 content: str, variables: List[str] = None):
        self.template_id = template_id
        self.name = name
        self.device_type = device_type
        self.content = content
        self.variables = variables or []
        self.created_at = datetime.now()

    def to_dict(self):
        return {
            'template_id': self.template_id,
            'name': self.name,
            'device_type': self.device_type,
            'content': self.content,
            'variables': self.variables,
            'created_at': self.created_at.isoformat()
        }


class ConfigTemplateService:
    """配置模板服务"""

    def __init__(self, config: Dict):
        self.config = config
        self.templates_dir = config.get('templates_dir', '/ztp/templates')
        self.templates: Dict[str, ConfigTemplate] = {}
        self.device_assignments: Dict[str, str] = {}  # mac_address -> template_id

        # 创建模板目录
        os.makedirs(self.templates_dir, exist_ok=True)

        # 加载默认模板
        self._load_default_templates()

    def _load_default_templates(self):
        """加载默认配置模板"""
        # 华为交换机默认模板
        switch_template = ConfigTemplate(
            template_id='default_switch',
            name='默认交换机配置',
            device_type='switch',
            content='''#
# 华为交换机默认配置模板
# 自动生成时间: {timestamp}
#

sysname {hostname}

vlan batch 10 20 30

interface Vlanif1
 ip address {ip_address} {subnet_mask}
 quit

interface GigabitEthernet0/0/1
 port link-type access
 port default vlan 10
 quit

interface GigabitEthernet0/0/2
 port link-type trunk
 port trunk allow-pass vlan 10 20 30
 quit

ssh server enable
stelnet server enable

local-user {username}
 password cipher {password}
 privilege level 15
 service-type ssh telnet
 quit

user-interface vty 0 4
 authentication-mode aaa
 protocol inbound ssh
 quit
''',
            variables=['hostname', 'ip_address', 'subnet_mask', 'username', 'password']
        )
        self.templates['default_switch'] = switch_template

        # 华为路由器默认模板
        router_template = ConfigTemplate(
            template_id='default_router',
            name='默认路由器配置',
            device_type='router',
            content='''#
# 华为路由器默认配置模板
# 自动生成时间: {timestamp}
#

sysname {hostname}

interface GigabitEthernet0/0/0
 ip address {wan_ip} {wan_mask}
 quit

interface GigabitEthernet0/0/1
 ip address {lan_ip} {lan_mask}
 quit

ip route-static 0.0.0.0 0.0.0.0 {gateway}

acl 2000
 rule permit source {lan_network} {lan_wildcard}
 quit

firewall enable
firewall packet-filter 2000 inbound

ssh server enable
stelnet server enable

local-user {username}
 password cipher {password}
 privilege level 15
 service-type ssh telnet
 quit
''',
            variables=['hostname', 'wan_ip', 'wan_mask', 'lan_ip', 'lan_mask',
                     'gateway', 'lan_network', 'lan_wildcard', 'username', 'password']
        )
        self.templates['default_router'] = router_template

        logger.info(f"加载了 {len(self.templates)} 个默认模板")

    def create_template(self, template_id: str, name: str, device_type: str,
                       content: str, variables: List[str] = None) -> ConfigTemplate:
        """创建新模板"""
        if template_id in self.templates:
            raise ValueError(f"模板 {template_id} 已存在")

        template = ConfigTemplate(template_id, name, device_type, content, variables)
        self.templates[template_id] = template

        # 保存到文件
        self._save_template_to_file(template)

        logger.info(f"创建模板: {template_id}")
        return template

    def update_template(self, template_id: str, **kwargs) -> ConfigTemplate:
        """更新模板"""
        if template_id not in self.templates:
            raise ValueError(f"模板 {template_id} 不存在")

        template = self.templates[template_id]
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)

        self._save_template_to_file(template)
        logger.info(f"更新模板: {template_id}")
        return template

    def delete_template(self, template_id: str):
        """删除模板"""
        if template_id not in self.templates:
            raise ValueError(f"模板 {template_id} 不存在")

        del self.templates[template_id]

        # 删除文件
        file_path = os.path.join(self.templates_dir, f"{template_id}.yaml")
        if os.path.exists(file_path):
            os.remove(file_path)

        logger.info(f"删除模板: {template_id}")

    def get_template(self, template_id: str) -> Optional[Dict]:
        """获取模板"""
        template = self.templates.get(template_id)
        if template:
            return template.to_dict()
        return None

    def list_templates(self) -> List[Dict]:
        """列出所有模板"""
        return [template.to_dict() for template in self.templates.values()]

    def assign_template_to_device(self, mac_address: str, template_id: str):
        """为设备分配模板"""
        if template_id not in self.templates:
            raise ValueError(f"模板 {template_id} 不存在")

        self.device_assignments[mac_address] = template_id
        logger.info(f"为设备 {mac_address} 分配模板 {template_id}")

    def get_config_for_device(self, mac_address: str, **variables) -> Optional[str]:
        """为设备生成配置"""
        template_id = self.device_assignments.get(mac_address)
        if not template_id:
            # 使用默认模板
            template_id = 'default_switch'

        template = self.templates.get(template_id)
        if not template:
            logger.warning(f"未找到模板 {template_id}")
            return None

        # 合并变量
        config_vars = {
            'timestamp': datetime.now().isoformat(),
            'mac_address': mac_address
        }
        config_vars.update(variables)

        # 替换模板变量
        try:
            config = template.content.format(**config_vars)
            logger.info(f"为设备 {mac_address} 生成配置，使用模板 {template_id}")
            return config
        except KeyError as e:
            logger.error(f"配置生成失败，缺少变量: {e}")
            return None

    def _save_template_to_file(self, template: ConfigTemplate):
        """保存模板到文件"""
        file_path = os.path.join(self.templates_dir, f"{template.template_id}.yaml")
        with open(file_path, 'w') as f:
            yaml.dump(template.to_dict(), f)

    def _load_templates_from_files(self):
        """从文件加载模板"""
        if not os.path.exists(self.templates_dir):
            return

        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.yaml'):
                file_path = os.path.join(self.templates_dir, filename)
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
                    template = ConfigTemplate(
                        template_id=data['template_id'],
                        name=data['name'],
                        device_type=data['device_type'],
                        content=data['content'],
                        variables=data.get('variables', [])
                    )
                    self.templates[template.template_id] = template

        logger.info(f"从文件加载了 {len(self.templates)} 个模板")


def main():
    """主函数"""
    config = {
        'templates_dir': '/ztp/templates'
    }
    service = ConfigTemplateService(config)

    # 测试生成配置
    config = service.get_config_for_device(
        '00:11:22:33:44:55',
        hostname='Switch-01',
        ip_address='192.168.1.100',
        subnet_mask='255.255.255.0',
        username='admin',
        password='Admin@123'
    )
    print(config)


if __name__ == '__main__':
    main()

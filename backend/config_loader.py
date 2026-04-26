"""
配置加载模块
优先从环境变量读取配置，如果没有则从 config.yaml 读取
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


def get_env(key: str, default: Any = None, cast_type: type = str) -> Any:
    """
    从环境变量获取配置值
    
    Args:
        key: 环境变量键名
        default: 默认值
        cast_type: 类型转换 (str, int, bool, float)
    
    Returns:
        配置值
    """
    value = os.getenv(key, default)
    if value is None:
        return default
    
    if cast_type == bool:
        return str(value).lower() in ('true', '1', 'yes', 'on')
    elif cast_type == int:
        return int(value)
    elif cast_type == float:
        return float(value)
    else:
        return value


def get_env_list(key: str, default: Any = None, separator: str = ',') -> list:
    """
    从环境变量获取列表配置值
    
    Args:
        key: 环境变量键名
        default: 默认值
        separator: 分隔符
    
    Returns:
        配置列表
    """
    value = os.getenv(key, default)
    if value is None:
        return default if default is not None else []
    
    return [item.strip() for item in str(value).split(separator) if item.strip()]


def load_config() -> Dict[str, Any]:
    """
    加载完整配置
    优先从环境变量读取，如果没有则从 config.yaml 读取
    
    Returns:
        完整配置字典
    """
    # 加载 config.yaml 作为基础配置
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}
    
    # 从环境变量覆盖配置
    config.update({
        'server': {
            'host': get_env('SERVER_HOST', config.get('server', {}).get('host', '0.0.0.0')),
            'port': get_env('SERVER_PORT', config.get('server', {}).get('port', 8000), int),
            'debug': get_env('DEBUG', config.get('server', {}).get('debug', False), bool),
        },
        'database': {
            'url': get_env('DATABASE_URL', config.get('database', {}).get('url', 'sqlite:///data/network.db')),
            'echo': get_env('DATABASE_ECHO', config.get('database', {}).get('echo', False), bool),
        },
        'security': {
            'jwt_secret': get_env('JWT_SECRET', config.get('security', {}).get('jwt_secret', 'your-jwt-secret')),
            'jwt_expire_hours': get_env('JWT_EXPIRE_HOURS', config.get('security', {}).get('jwt_expire_hours', 24), int),
            'api_rate_limit': get_env('API_RATE_LIMIT', config.get('security', {}).get('api_rate_limit', 100), int),
        },
        'huawei': {
            'default_username': get_env('HUAWEI_DEFAULT_USERNAME', config.get('huawei', {}).get('default_username', 'admin')),
            'default_password': get_env('HUAWEI_DEFAULT_PASSWORD', config.get('huawei', {}).get('default_password', 'Admin@123')),
            'ssh_port': get_env('HUAWEI_SSH_PORT', config.get('huawei', {}).get('ssh_port', 22), int),
            'connection_timeout': get_env('HUAWEI_CONNECTION_TIMEOUT', config.get('huawei', {}).get('connection_timeout', 30), int),
            'command_timeout': get_env('HUAWEI_COMMAND_TIMEOUT', config.get('huawei', {}).get('command_timeout', 60), int),
        },
        'monitoring': {
            'check_interval': get_env('MONITORING_CHECK_INTERVAL', config.get('monitoring', {}).get('check_interval', 60), int),
            'cpu_threshold': get_env('MONITORING_CPU_THRESHOLD', config.get('monitoring', {}).get('cpu_threshold', 80), int),
            'memory_threshold': get_env('MONITORING_MEMORY_THRESHOLD', config.get('monitoring', {}).get('memory_threshold', 85), int),
            'bandwidth_threshold': get_env('MONITORING_BANDWIDTH_THRESHOLD', config.get('monitoring', {}).get('bandwidth_threshold', 90), int),
            'latency_threshold': get_env('MONITORING_LATENCY_THRESHOLD', config.get('monitoring', {}).get('latency_threshold', 100), int),
            'packet_loss_threshold': get_env('MONITORING_PACKET_LOSS_THRESHOLD', config.get('monitoring', {}).get('packet_loss_threshold', 1), int),
        },
        'auto_optimization': {
            'enabled': get_env('AUTO_OPTIMIZATION_ENABLED', config.get('auto_optimization', {}).get('enabled', True), bool),
            'check_interval': get_env('AUTO_OPTIMIZATION_CHECK_INTERVAL', config.get('auto_optimization', {}).get('check_interval', 300), int),
            'enable_route_optimization': get_env('AUTO_OPTIMIZATION_ENABLE_ROUTE', config.get('auto_optimization', {}).get('enable_route_optimization', True), bool),
            'enable_bandwidth_management': get_env('AUTO_OPTIMIZATION_ENABLE_BANDWIDTH', config.get('auto_optimization', {}).get('enable_bandwidth_management', True), bool),
            'enable_load_balancing': get_env('AUTO_OPTIMIZATION_ENABLE_LOAD_BALANCE', config.get('auto_optimization', {}).get('enable_load_balancing', True), bool),
        },
        'notifications': {
            'wechat': {
                'enabled': get_env('WECHAT_ENABLED', config.get('notifications', {}).get('wechat', {}).get('enabled', True), bool),
                'corp_id': get_env('WECHAT_CORP_ID', config.get('notifications', {}).get('wechat', {}).get('corp_id', '')),
                'agent_id': get_env('WECHAT_AGENT_ID', config.get('notifications', {}).get('wechat', {}).get('agent_id', '')),
                'secret': get_env('WECHAT_SECRET', config.get('notifications', {}).get('wechat', {}).get('secret', '')),
            },
            'sms': {
                'enabled': get_env('SMS_ENABLED', config.get('notifications', {}).get('sms', {}).get('enabled', True), bool),
                'access_key_id': get_env('SMS_ACCESS_KEY_ID', config.get('notifications', {}).get('sms', {}).get('access_key_id', '')),
                'access_key_secret': get_env('SMS_ACCESS_KEY_SECRET', config.get('notifications', {}).get('sms', {}).get('access_key_secret', '')),
                'sign_name': get_env('SMS_SIGN_NAME', config.get('notifications', {}).get('sms', {}).get('sign_name', '网络运维')),
                'template_code': get_env('SMS_TEMPLATE_CODE', config.get('notifications', {}).get('sms', {}).get('template_code', '')),
            },
            'email': {
                'enabled': get_env('EMAIL_ENABLED', config.get('notifications', {}).get('email', {}).get('enabled', True), bool),
                'smtp_server': get_env('SMTP_SERVER', config.get('notifications', {}).get('email', {}).get('smtp_server', '')),
                'smtp_port': get_env('SMTP_PORT', config.get('notifications', {}).get('email', {}).get('smtp_port', 587), int),
                'smtp_username': get_env('SMTP_USERNAME', config.get('notifications', {}).get('email', {}).get('smtp_username', '')),
                'smtp_password': get_env('SMTP_PASSWORD', config.get('notifications', {}).get('email', {}).get('smtp_password', '')),
                'from_address': get_env('FROM_ADDRESS', config.get('notifications', {}).get('email', {}).get('from_address', '')),
                'to_addresses': get_env_list('TO_ADDRESSES', config.get('notifications', {}).get('email', {}).get('to_addresses', [])),
            },
        },
        'logging': {
            'level': get_env('LOG_LEVEL', config.get('logging', {}).get('level', 'INFO')),
            'file': get_env('LOG_FILE', config.get('logging', {}).get('file', 'logs/network-auto.log')),
            'max_size': get_env('LOG_MAX_SIZE', config.get('logging', {}).get('max_size', 100), int),
            'backup_count': get_env('LOG_BACKUP_COUNT', config.get('logging', {}).get('backup_count', 10), int),
        },
        'ztp': {
            'enabled': get_env('ZTP_ENABLED', config.get('ztp', {}).get('enabled', True), bool),
            'dhcp': {
                'enabled': get_env('ZTP_DHCP_ENABLED', config.get('ztp', {}).get('dhcp', {}).get('enabled', True), bool),
                'server_ip': get_env('ZTP_DHCP_SERVER_IP', config.get('ztp', {}).get('dhcp', {}).get('server_ip', '192.168.1.10')),
                'lease_start': get_env('ZTP_DHCP_LEASE_START', config.get('ztp', {}).get('dhcp', {}).get('lease_start', '192.168.1.100')),
                'lease_end': get_env('ZTP_DHCP_LEASE_END', config.get('ztp', {}).get('dhcp', {}).get('lease_end', '192.168.1.200')),
                'subnet_mask': get_env('ZTP_DHCP_SUBNET_MASK', config.get('ztp', {}).get('dhcp', {}).get('subnet_mask', '255.255.255.0')),
                'gateway': get_env('ZTP_DHCP_GATEWAY', config.get('ztp', {}).get('dhcp', {}).get('gateway', '192.168.1.1')),
                'dns_server': get_env('ZTP_DHCP_DNS_SERVER', config.get('ztp', {}).get('dhcp', {}).get('dns_server', '8.8.8.8')),
                'lease_time': get_env('ZTP_DHCP_LEASE_TIME', config.get('ztp', {}).get('dhcp', {}).get('lease_time', 86400), int),
            },
            'tftp': {
                'enabled': get_env('ZTP_TFTP_ENABLED', config.get('ztp', {}).get('tftp', {}).get('enabled', True), bool),
                'port': get_env('ZTP_TFTP_PORT', config.get('ztp', {}).get('tftp', {}).get('port', 69), int),
                'root_dir': get_env('ZTP_TFTP_ROOT_DIR', config.get('ztp', {}).get('tftp', {}).get('root_dir', '/tftpboot')),
                'server_ip': get_env('ZTP_TFTP_SERVER_IP', config.get('ztp', {}).get('tftp', {}).get('server_ip', '192.168.1.10')),
            },
            'http': {
                'enabled': get_env('ZTP_HTTP_ENABLED', config.get('ztp', {}).get('http', {}).get('enabled', True), bool),
                'port': get_env('ZTP_HTTP_PORT', config.get('ztp', {}).get('http', {}).get('port', 8080), int),
                'server_url': get_env('ZTP_HTTP_SERVER_URL', config.get('ztp', {}).get('http', {}).get('server_url', 'http://192.168.1.10:8080')),
            },
            'discovery': {
                'enabled': get_env('ZTP_DISCOVERY_ENABLED', config.get('ztp', {}).get('discovery', {}).get('enabled', True), bool),
                'interface': get_env('ZTP_DISCOVERY_INTERFACE', config.get('ztp', {}).get('discovery', {}).get('interface')),
                'scan_interval': get_env('ZTP_DISCOVERY_SCAN_INTERVAL', config.get('ztp', {}).get('discovery', {}).get('scan_interval', 60), int),
                'max_age_hours': get_env('ZTP_DISCOVERY_MAX_AGE_HOURS', config.get('ztp', {}).get('discovery', {}).get('max_age_hours', 24), int),
            },
            'templates': {
                'dir': get_env('ZTP_TEMPLATES_DIR', config.get('ztp', {}).get('templates', {}).get('dir', '/ztp/templates')),
                'default_switch_template': get_env('ZTP_DEFAULT_SWITCH_TEMPLATE', config.get('ztp', {}).get('templates', {}).get('default_switch_template', 'default_switch')),
                'default_router_template': get_env('ZTP_DEFAULT_ROUTER_TEMPLATE', config.get('ztp', {}).get('templates', {}).get('default_router_template', 'default_router')),
            },
        },
    })
    
    return config


# 全局配置实例
config = load_config()

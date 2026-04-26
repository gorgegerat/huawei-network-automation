#!/usr/bin/env python3
"""
ZTP零接触部署主服务
集成DHCP、TFTP、HTTP、设备发现和配置模板服务
"""

import logging
import signal
import sys
from typing import Dict
from dhcp_server import DHCPServer
from tftp_server import TFTPServer
from http_server import ZTPHTTPServer, ztp_server as http_ztp_server
from config_template_service import ConfigTemplateService
from device_discovery import DeviceDiscoveryService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ZTPService:
    """ZTP零接触部署服务"""

    def __init__(self, config: Dict):
        self.config = config
        self.running = False

        # 初始化各个服务
        self.config_service = ConfigTemplateService({
            'templates_dir': config.get('templates_dir', '/ztp/templates')
        })

        self.tftp_server = TFTPServer({
            'listen_port': config.get('tftp_port', 69),
            'root_dir': config.get('tftp_root', '/tftpboot')
        })
        self.tftp_server.set_config_service(self.config_service)

        self.device_discovery = DeviceDiscoveryService({
            'interface': config.get('discovery_interface', None),
            'scan_interval': config.get('discovery_interval', 60)
        })

        # 设置HTTP服务器的配置服务
        global http_ztp_server
        http_ztp_server = ZTPHTTPServer({
            'listen_port': config.get('http_port', 8080)
        })
        http_ztp_server.set_config_service(self.config_service)

        # DHCP服务器（简化版，实际建议使用dnsmasq）
        self.dhcp_server = DHCPServer({
            'server_ip': config.get('server_ip', '192.168.1.10'),
            'lease_start': config.get('lease_start', '192.168.1.100'),
            'lease_end': config.get('lease_end', '192.168.1.200'),
            'subnet_mask': config.get('subnet_mask', '255.255.255.0'),
            'gateway': config.get('gateway', '192.168.1.1'),
            'dns_server': config.get('dns_server', '8.8.8.8'),
            'tftp_server': config.get('tftp_server', '192.168.1.10'),
            'http_server': config.get('http_server', 'http://192.168.1.10:8080'),
            'lease_time': config.get('lease_time', 86400)
        })

    def start(self):
        """启动所有ZTP服务"""
        logger.info("启动ZTP零接触部署服务...")
        self.running = True

        # 启动配置模板服务
        logger.info("配置模板服务已就绪")

        # 启动TFTP服务器
        self.tftp_server.start()

        # 启动设备发现服务
        self.device_discovery.start()

        # 启动DHCP服务器
        self.dhcp_server.start()

        # HTTP服务器在单独的进程中运行
        logger.info("HTTP服务器将在独立进程中运行")

        logger.info("ZTP服务启动完成")
        logger.info(f"TFTP服务器: 端口 {self.config.get('tftp_port', 69)}")
        logger.info(f"HTTP服务器: 端口 {self.config.get('http_port', 8080)}")
        logger.info(f"设备发现: 扫描间隔 {self.config.get('discovery_interval', 60)}秒")

    def stop(self):
        """停止所有ZTP服务"""
        logger.info("停止ZTP服务...")
        self.running = False

        self.tftp_server.stop()
        self.device_discovery.stop()
        self.dhcp_server.stop()

        logger.info("ZTP服务已停止")

    def get_status(self) -> Dict:
        """获取服务状态"""
        discovered_devices = self.device_discovery.get_discovered_devices()
        templates = self.config_service.list_templates()

        return {
            'running': self.running,
            'discovered_devices': len(discovered_devices),
            'templates': len(templates),
            'tftp_server': self.tftp_server.running,
            'device_discovery': self.device_discovery.running,
            'dhcp_server': self.dhcp_server.running
        }


def signal_handler(signum, frame):
    """信号处理"""
    logger.info(f"收到信号 {signum}, 正在停止服务...")
    if ztp_service:
        ztp_service.stop()
    sys.exit(0)


def main():
    """主函数"""
    # 配置
    config = {
        'server_ip': '192.168.1.10',
        'lease_start': '192.168.1.100',
        'lease_end': '192.168.1.200',
        'subnet_mask': '255.255.255.0',
        'gateway': '192.168.1.1',
        'dns_server': '8.8.8.8',
        'tftp_server': '192.168.1.10',
        'http_server': 'http://192.168.1.10:8080',
        'lease_time': 86400,
        'tftp_port': 69,
        'tftp_root': '/tftpboot',
        'http_port': 8080,
        'templates_dir': '/ztp/templates',
        'discovery_interface': None,
        'discovery_interval': 60
    }

    global ztp_service
    ztp_service = ZTPService(config)

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动服务
    ztp_service.start()

    try:
        # 主循环
        while ztp_service.running:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        ztp_service.stop()


if __name__ == '__main__':
    main()

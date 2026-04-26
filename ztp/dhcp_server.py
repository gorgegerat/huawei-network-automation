#!/usr/bin/env python3
"""
ZTP DHCP服务器
为新设备提供DHCP服务，返回配置服务器地址
"""

import socket
import struct
from typing import Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DHCPServer:
    """简单的DHCP服务器实现"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.server_ip = config.get('server_ip', '192.168.1.10')
        self.lease_start = config.get('lease_start', '192.168.1.100')
        self.lease_end = config.get('lease_end', '192.168.1.200')
        self.subnet_mask = config.get('subnet_mask', '255.255.255.0')
        self.gateway = config.get('gateway', '192.168.1.1')
        self.dns_server = config.get('dns_server', '8.8.8.8')
        self.tftp_server = config.get('tftp_server', '192.168.1.10')
        self.http_server = config.get('http_server', 'http://192.168.1.10:8080')
        self.lease_time = config.get('lease_time', 86400)  # 24小时

        self.leases: Dict[str, Dict[str, Any]] = {}
        self.running = False

    def start(self):
        """启动DHCP服务器"""
        self.running = True
        logger.info(f"DHCP服务器启动，监听端口 67")
        logger.info(f"IP池: {self.lease_start} - {self.lease_end}")
        logger.info(f"TFTP服务器: {self.tftp_server}")
        logger.info(f"HTTP服务器: {self.http_server}")

    def stop(self):
        """停止DHCP服务器"""
        self.running = False
        logger.info("DHCP服务器已停止")

    def allocate_ip(self, mac_address: str) -> Optional[str]:
        """为设备分配IP地址"""
        # 检查是否已有租约
        if mac_address in self.leases:
            return self.leases[mac_address]['ip']

        # 分配新IP
        ip_parts = self.lease_start.split('.')
        last_octet = int(ip_parts[3])
        end_octet = int(self.lease_end.split('.')[3])

        while last_octet <= end_octet:
            ip = f"{'.'.join(ip_parts[:3])}.{last_octet}"
            # 检查IP是否已被分配
            if not any(lease['ip'] == ip for lease in self.leases.values()):
                self.leases[mac_address] = {
                    'ip': ip,
                    'mac': mac_address,
                    'lease_time': self.lease_time
                }
                logger.info(f"为MAC {mac_address} 分配IP: {ip}")
                return ip
            last_octet += 1

        logger.warning(f"IP池已耗尽，无法为 {mac_address} 分配IP")
        return None

    def create_dhcp_offer(self, mac_address: str, xid: int) -> bytes:
        """创建DHCP OFFER数据包"""
        ip = self.allocate_ip(mac_address)
        if not ip:
            return None

        # DHCP OFFER数据包构造
        # 这里简化实现，实际需要完整的DHCP协议实现
        # 建议使用dnsmasq或isc-dhcp-server等专业DHCP服务器

        logger.info(f"发送DHCP OFFER给 {mac_address}: IP={ip}")
        return b''  # 实际实现需要返回完整的DHCP数据包

    def create_dhcp_ack(self, mac_address: str, xid: int) -> bytes:
        """创建DHCP ACK数据包，包含ZTP选项"""
        ip = self.leases.get(mac_address, {}).get('ip')
        if not ip:
            return None

        # DHCP ACK数据包构造
        # 包含ZTP相关选项：
        # - Option 66: TFTP服务器地址
        # - Option 67: 启动文件名
        # - Option 150: TFTP服务器地址（华为使用）
        # - 自定义选项: HTTP配置服务器地址

        logger.info(f"发送DHCP ACK给 {mac_address}: IP={ip}, TFTP={self.tftp_server}")
        return b''  # 实际实现需要返回完整的DHCP数据包


def main():
    """主函数"""
    config = {
        'server_ip': '192.168.1.10',
        'lease_start': '192.168.1.100',
        'lease_end': '192.168.1.200',
        'subnet_mask': '255.255.255.0',
        'gateway': '192.168.1.1',
        'dns_server': '8.8.8.8',
        'tftp_server': '192.168.1.10',
        'http_server': 'http://192.168.1.10:8080',
        'lease_time': 86400
    }

    server = DHCPServer(config)
    server.start()

    try:
        while server.running:
            # 实际实现需要监听UDP 67端口
            # 处理DHCP DISCOVER, REQUEST等消息
            pass
    except KeyboardInterrupt:
        server.stop()


if __name__ == '__main__':
    main()

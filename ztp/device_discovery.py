#!/usr/bin/env python3
"""
ZTP设备自动发现服务
监听网络，自动发现新设备
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import scapy.all as scapy
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveredDevice:
    """发现的设备"""

    def __init__(self, mac_address: str, ip_address: str = None):
        self.mac_address = mac_address
        self.ip_address = ip_address
        self.device_type = None
        self.vendor = self._get_vendor(mac_address)
        self.first_seen = datetime.now()
        self.last_seen = datetime.now()
        self.status = 'discovered'

    def _get_vendor(self, mac_address: str) -> str:
        """根据MAC地址获取厂商"""
        # 华为MAC地址前缀
        huawei_prefixes = [
            '00:E0:FC', '00:E0:0C', '00:1A:A0', '00:25:9E',
            '00:1B:0E', '00:22:91', '00:23:24', '00:25:B3'
        ]

        mac_prefix = ':'.join(mac_address.split(':')[:3]).upper()
        if mac_prefix in huawei_prefixes:
            return 'Huawei'

        return 'Unknown'

    def to_dict(self):
        return {
            'mac_address': self.mac_address,
            'ip_address': self.ip_address,
            'device_type': self.device_type,
            'vendor': self.vendor,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'status': self.status
        }


class DeviceDiscoveryService:
    """设备发现服务"""

    def __init__(self, config: Dict):
        self.config = config
        self.interface = config.get('interface', None)
        self.discovered_devices: Dict[str, DiscoveredDevice] = {}
        self.running = False
        self.discovery_thread = None

    def start(self):
        """启动设备发现"""
        self.running = True
        self.discovery_thread = threading.Thread(target=self._discovery_loop)
        self.discovery_thread.daemon = True
        self.discovery_thread.start()
        logger.info("设备发现服务启动")

    def stop(self):
        """停止设备发现"""
        self.running = False
        if self.discovery_thread:
            self.discovery_thread.join(timeout=5)
        logger.info("设备发现服务停止")

    def _discovery_loop(self):
        """发现循环"""
        while self.running:
            try:
                self._scan_network()
                time.sleep(self.config.get('scan_interval', 60))
            except Exception as e:
                logger.error(f"设备发现错误: {e}")

    def _scan_network(self):
        """扫描网络"""
        logger.info("扫描网络中的设备...")

        # 使用ARP扫描
        try:
            # 获取网络接口
            if self.interface:
                scapy.conf.iface = self.interface

            # ARP扫描
            arp_packet = scapy.Ether(dst="ff:ff:ff:ff:ff:ff") / scapy.ARP(pdst="192.168.1.0/24")
            result = scapy.srp(arp_packet, timeout=2, verbose=False)[0]

            for sent, received in result:
                mac_address = received.hwsrc
                ip_address = received.psrc

                self._register_device(mac_address, ip_address)

        except Exception as e:
            logger.error(f"ARP扫描失败: {e}")

    def _register_device(self, mac_address: str, ip_address: str):
        """注册发现的设备"""
        if mac_address not in self.discovered_devices:
            device = DiscoveredDevice(mac_address, ip_address)
            self.discovered_devices[mac_address] = device
            logger.info(f"发现新设备: {mac_address} ({ip_address}) - {device.vendor}")
        else:
            # 更新最后发现时间
            self.discovered_devices[mac_address].last_seen = datetime.now()
            if ip_address:
                self.discovered_devices[mac_address].ip_address = ip_address

    def get_discovered_devices(self) -> List[Dict]:
        """获取所有发现的设备"""
        return [device.to_dict() for device in self.discovered_devices.values()]

    def get_device(self, mac_address: str) -> Optional[Dict]:
        """获取特定设备信息"""
        device = self.discovered_devices.get(mac_address)
        if device:
            return device.to_dict()
        return None

    def clear_old_devices(self, max_age_hours: int = 24):
        """清除旧设备"""
        now = datetime.now()
        to_remove = []

        for mac_address, device in self.discovered_devices.items():
            age = (now - device.last_seen).total_seconds() / 3600
            if age > max_age_hours:
                to_remove.append(mac_address)

        for mac_address in to_remove:
            del self.discovered_devices[mac_address]
            logger.info(f"清除旧设备: {mac_address}")

        if to_remove:
            logger.info(f"清除了 {len(to_remove)} 个旧设备")


def main():
    """主函数"""
    config = {
        'interface': None,
        'scan_interval': 60
    }
    service = DeviceDiscoveryService(config)
    service.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        service.stop()

    # 打印发现的设备
    devices = service.get_discovered_devices()
    print(f"发现的设备: {len(devices)}")
    for device in devices:
        print(f"  {device['mac_address']} - {device['vendor']}")


if __name__ == '__main__':
    main()

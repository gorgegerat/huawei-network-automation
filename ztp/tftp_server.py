#!/usr/bin/env python3
"""
ZTP TFTP服务器
为设备提供配置文件下载服务
"""

import os
import logging
from typing import Dict, Optional
from tftpy import TftpServer, TftpHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZTPTftpHandler(TftpHandler):
    """自定义TFTP处理器，支持动态配置生成"""

    def __init__(self, *args, **kwargs):
        self.config_service = kwargs.pop('config_service', None)
        super().__init__(*args, **kwargs)

    def get_file(self, filename: str) -> Optional[bytes]:
        """获取配置文件内容"""
        logger.info(f"请求配置文件: {filename}")

        # 如果配置服务可用，动态生成配置
        if self.config_service:
            try:
                # 从文件名解析设备信息
                # 例如: config_<mac_address>.cfg
                if filename.startswith('config_') and filename.endswith('.cfg'):
                    mac_address = filename[7:-4]
                    config = self.config_service.get_config_for_device(mac_address)
                    if config:
                        logger.info(f"为设备 {mac_address} 生成配置")
                        return config.encode('utf-8')
            except Exception as e:
                logger.error(f"生成配置失败: {e}")

        # 否则从文件系统读取
        file_path = os.path.join(self.root, filename)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return f.read()

        logger.warning(f"配置文件不存在: {filename}")
        return None


class TFTPServer:
    """TFTP服务器"""

    def __init__(self, config: Dict):
        self.config = config
        self.listen_port = config.get('listen_port', 69)
        self.root_dir = config.get('root_dir', '/tftpboot')
        self.config_service = None
        self.server = None
        self.running = False

    def set_config_service(self, config_service):
        """设置配置服务"""
        self.config_service = config_service

    def start(self):
        """启动TFTP服务器"""
        # 创建TFTP根目录
        os.makedirs(self.root_dir, exist_ok=True)

        # 创建自定义处理器
        handler = ZTPTftpHandler
        handler.root = self.root_dir
        handler.config_service = self.config_service

        # 启动TFTP服务器
        self.server = TftpServer(('0.0.0.0', self.listen_port), handler)
        self.running = True
        logger.info(f"TFTP服务器启动，监听端口 {self.listen_port}")
        logger.info(f"TFTP根目录: {self.root_dir}")

    def stop(self):
        """停止TFTP服务器"""
        if self.server:
            self.server.close()
        self.running = False
        logger.info("TFTP服务器已停止")

    def add_config_file(self, filename: str, content: str):
        """添加配置文件"""
        file_path = os.path.join(self.root_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        logger.info(f"添加配置文件: {filename}")

    def remove_config_file(self, filename: str):
        """删除配置文件"""
        file_path = os.path.join(self.root_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"删除配置文件: {filename}")


def main():
    """主函数"""
    config = {
        'listen_port': 69,
        'root_dir': '/tftpboot'
    }

    server = TFTPServer(config)
    server.start()

    try:
        while server.running:
            pass
    except KeyboardInterrupt:
        server.stop()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
ZTP HTTP服务器
为设备提供配置文件下载和注册服务
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Dict, Optional
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ZTP HTTP Server")


class ZTPHTTPServer:
    """ZTP HTTP服务器"""

    def __init__(self, config: Dict):
        self.config = config
        self.listen_port = config.get('listen_port', 8080)
        self.config_service = None
        self.device_registry: Dict[str, Dict] = {}

    def set_config_service(self, config_service):
        """设置配置服务"""
        self.config_service = config_service

    def start(self):
        """启动HTTP服务器"""
        import uvicorn
        logger.info(f"HTTP服务器启动，监听端口 {self.listen_port}")
        uvicorn.run(app, host='0.0.0.0', port=self.listen_port)

    def register_device(self, mac_address: str, device_info: Dict):
        """注册新设备"""
        self.device_registry[mac_address] = {
            'info': device_info,
            'status': 'registered',
            'registered_at': None
        }
        logger.info(f"注册新设备: {mac_address}")
        return self.device_registry[mac_address]


# 全局服务器实例
ztp_server = None


@app.on_event("startup")
async def startup():
    """启动事件"""
    global ztp_server
    logger.info("ZTP HTTP服务器启动")


@app.get("/")
async def root():
    """根路径"""
    return {"message": "ZTP HTTP Server", "status": "running"}


@app.get("/config/{filename}", response_class=PlainTextResponse)
async def get_config(filename: str):
    """获取配置文件"""
    logger.info(f"请求配置文件: {filename}")

    if ztp_server and ztp_server.config_service:
        # 动态生成配置
        if filename.startswith('config_') and filename.endswith('.cfg'):
            mac_address = filename[7:-4]
            config = ztp_server.config_service.get_config_for_device(mac_address)
            if config:
                logger.info(f"为设备 {mac_address} 返回配置")
                return config

    raise HTTPException(status_code=404, detail="配置文件不存在")


@app.get("/api/v1/device/{mac_address}/config")
async def get_device_config(mac_address: str):
    """获取设备配置（API方式）"""
    if ztp_server and ztp_server.config_service:
        config = ztp_server.config_service.get_config_for_device(mac_address)
        if config:
            return {"config": config}

    raise HTTPException(status_code=404, detail="设备配置不存在")


@app.post("/api/v1/device/register")
async def register_device(request: Request):
    """设备注册接口"""
    data = await request.json()
    mac_address = data.get('mac_address')
    device_info = data.get('device_info', {})

    if not mac_address:
        raise HTTPException(status_code=400, detail="缺少MAC地址")

    if ztp_server:
        result = ztp_server.register_device(mac_address, device_info)
        return {"status": "success", "data": result}

    raise HTTPException(status_code=500, detail="服务器未初始化")


@app.get("/api/v1/templates")
async def list_templates():
    """列出所有配置模板"""
    if ztp_server and ztp_server.config_service:
        templates = ztp_server.config_service.list_templates()
        return {"templates": templates}

    raise HTTPException(status_code=500, detail="服务器未初始化")


@app.get("/api/v1/template/{template_id}")
async def get_template(template_id: str):
    """获取配置模板"""
    if ztp_server and ztp_server.config_service:
        template = ztp_server.config_service.get_template(template_id)
        if template:
            return template

    raise HTTPException(status_code=404, detail="模板不存在")


def main():
    """主函数"""
    global ztp_server
    config = {
        'listen_port': 8080
    }
    ztp_server = ZTPHTTPServer(config)
    ztp_server.start()


if __name__ == '__main__':
    main()

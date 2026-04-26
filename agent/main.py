#!/usr/bin/env python3
"""
华为设备代理 - 运行在设备上或管理服务器上
负责自动发现设备、从云端拉取配置、自动部署
"""

import asyncio
import yaml
import sys
import os
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.device_discovery import DeviceDiscovery
from services.config_fetcher import ConfigFetcher
from services.auto_deployer import AutoDeployer

# 加载配置
config_path = Path("/app/config/config.yaml")
if not config_path.exists():
    config_path = Path("../config/config.yaml")

with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

class DeviceAgent:
    """设备代理主程序"""
    
    def __init__(self, config):
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self.discovery = DeviceDiscovery(config)
        self.config_fetcher = ConfigFetcher(config)
        self.auto_deployer = AutoDeployer(config)
        self.running = False
    
    async def start(self):
        """启动代理"""
        print("启动华为设备代理...")
        
        # 添加定时任务
        check_interval = config.get("agent", {}).get("check_interval", 60)
        
        # 设备发现任务
        self.scheduler.add_job(
            self.discover_and_deploy,
            'interval',
            seconds=check_interval,
            id='discover_and_deploy'
        )
        
        # 配置同步任务
        self.scheduler.add_job(
            self.sync_configs,
            'interval',
            seconds=check_interval * 5,
            id='sync_configs'
        )
        
        self.scheduler.start()
        self.running = True
        
        print("设备代理已启动")
        
        # 首次运行
        await self.discover_and_deploy()
        
        # 保持运行
        while self.running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """停止代理"""
        self.running = False
        self.scheduler.shutdown()
        print("设备代理已停止")
    
    async def discover_and_deploy(self):
        """发现新设备并自动部署"""
        print("开始设备发现...")
        
        try:
            # 扫描网络中的华为设备
            devices = await self.discovery.scan_network()
            
            for device in devices:
                print(f"发现设备: {device['ip']} ({device.get('model', 'Unknown')})")
                
                # 检查设备是否已注册
                registered = await self.config_fetcher.check_device_registered(device['ip'])
                
                if not registered:
                    print(f"设备 {device['ip']} 未注册，开始自动部署...")
                    
                    # 从云端获取配置
                    device_config = await self.config_fetcher.fetch_config_for_device(device)
                    
                    if device_config:
                        # 自动部署配置
                        result = await self.auto_deployer.deploy(device, device_config)
                        
                        if result['success']:
                            print(f"设备 {device['ip']} 部署成功")
                            # 注册设备
                            await self.config_fetcher.register_device(device, result)
                        else:
                            print(f"设备 {device['ip']} 部署失败: {result['error']}")
                    else:
                        print(f"未找到设备 {device['ip']} 的配置模板")
                else:
                    print(f"设备 {device['ip']} 已注册")
                    
        except Exception as e:
            print(f"设备发现失败: {str(e)}")
    
    async def sync_configs(self):
        """同步配置"""
        print("开始配置同步...")
        
        try:
            # 获取所有已注册设备
            devices = await self.config_fetcher.get_registered_devices()
            
            for device in devices:
                # 检查配置是否需要更新
                needs_update = await self.config_fetcher.check_config_update(device)
                
                if needs_update:
                    print(f"设备 {device['ip']} 配置需要更新")
                    
                    # 获取新配置
                    new_config = await self.config_fetcher.fetch_config_for_device(device)
                    
                    if new_config:
                        # 应用新配置
                        result = await self.auto_deployer.apply_config(device, new_config)
                        
                        if result['success']:
                            print(f"设备 {device['ip']} 配置更新成功")
                        else:
                            print(f"设备 {device['ip']} 配置更新失败: {result['error']}")
        
        except Exception as e:
            print(f"配置同步失败: {str(e)}")

async def main():
    agent = DeviceAgent(config)
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        print("\n收到停止信号")
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())

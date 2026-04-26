from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn

from database import init_db, get_db
from routers import devices, configs, monitoring, alerts, auth, optimization, ztp
from services.notification_service import NotificationService
from services.monitor_service import MonitorService
from services.auto_optimization_service import AutoOptimizationService
from config_loader import config

# 初始化服务
notification_service = NotificationService(config)
monitor_service = MonitorService(config, notification_service)
auto_optimization_service = AutoOptimizationService(config, notification_service)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    await init_db()
    # 启动监控服务
    await monitor_service.start()
    # 启动自动优化服务
    await auto_optimization_service.start()
    yield
    # 关闭时清理
    await monitor_service.stop()
    await auto_optimization_service.stop()

# 创建FastAPI应用
app = FastAPI(
    title="华为网络设备自动化运维系统",
    description="提供华为企业网络设备的自动化部署、监控、优化和告警功能",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(devices.router, prefix="/api/devices", tags=["设备管理"])
app.include_router(configs.router, prefix="/api/configs", tags=["配置管理"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["监控"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["告警"])
app.include_router(optimization.router, prefix="/api/optimization", tags=["自动优化"])
app.include_router(ztp.router, prefix="/api", tags=["ZTP零接触部署"])

@app.get("/")
async def root():
    return {
        "message": "华为网络设备自动化运维系统API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.get("server", {}).get("host", "0.0.0.0"),
        port=config.get("server", {}).get("port", 8000),
        reload=config.get("server", {}).get("debug", False)
    )

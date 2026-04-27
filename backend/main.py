from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import init_db, get_db
from routers import devices, configs, monitoring, alerts, auth, optimization, ztp
from services.notification_service import NotificationService
from services.monitor_service import MonitorService
from services.auto_optimization_service import AutoOptimizationService
from services.docker_cleanup_service import DockerCleanupService
from config_loader import config

# 初始化日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化速率限制器
limiter = Limiter(key_func=get_remote_address)

# 初始化服务
notification_service = NotificationService(config)
monitor_service = MonitorService(config, notification_service)
auto_optimization_service = AutoOptimizationService(config, notification_service)
docker_cleanup_service = DockerCleanupService(config)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    await init_db()
    # 启动监控服务
    await monitor_service.start()
    # 启动自动优化服务
    await auto_optimization_service.start()
    # 启动Docker清理服务定时任务
    import asyncio
    async def cleanup_task():
        while True:
            try:
                await asyncio.sleep(docker_cleanup_service.schedule_hours * 3600)
                await docker_cleanup_service.full_cleanup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Docker清理任务失败: {e}")
    
    cleanup_task_handle = asyncio.create_task(cleanup_task())
    yield
    # 关闭时清理
    cleanup_task_handle.cancel()
    await monitor_service.stop()
    await auto_optimization_service.stop()

# 创建FastAPI应用
app = FastAPI(
    title="华为网络设备自动化运维系统",
    description="提供华为企业网络设备的自动化部署、监控、优化和告警功能",
    version="1.0.0",
    lifespan=lifespan
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
app.include_router(ztp.router, prefix="/api/ztp", tags=["ZTP"])

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "monitoring": "running" if monitor_service.is_running else "stopped",
            "auto_optimization": "running" if auto_optimization_service.is_running else "stopped",
            "docker_cleanup": docker_cleanup_service.get_status()
        }
    }

@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "华为网络设备自动化运维系统API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.get("server", {}).get("host", "0.0.0.0"),
        port=config.get("server", {}).get("port", 8000),
        reload=config.get("server", {}).get("debug", False)
    )

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
from contextlib import contextmanager
from config_loader import config

# 从配置加载器获取数据库配置
DATABASE_URL = config.get("database", {}).get("url", "sqlite:///data/network.db")

# 创建数据库引擎
engine = create_engine(DATABASE_URL, echo=config.get("database", {}).get("echo", False))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 数据库模型
class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(50), unique=True, nullable=False, index=True)
    device_type = Column(String(50), nullable=False)  # switch, router, firewall
    model = Column(String(100))
    serial_number = Column(String(100), unique=True)
    username = Column(String(50))
    password = Column(String(200))  # 加密存储
    ssh_port = Column(Integer, default=22)
    status = Column(String(20), default="offline")  # online, offline, error
    last_seen = Column(DateTime)
    group = Column(String(50), default="未分组")  # 设备分组
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 关系
    configs = relationship("DeviceConfig", back_populates="device", cascade="all, delete-orphan")
    metrics = relationship("DeviceMetric", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device", cascade="all, delete-orphan")

class DeviceConfig(Base):
    __tablename__ = "device_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    config_name = Column(String(100), nullable=False)
    config_content = Column(Text, nullable=False)
    version = Column(String(50))
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关系
    device = relationship("Device", back_populates="configs")

class DeviceMetric(Base):
    __tablename__ = "device_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    metric_type = Column(String(50), nullable=False)  # cpu, memory, bandwidth, latency, packet_loss
    metric_value = Column(Float, nullable=False)
    unit = Column(String(20))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # 关系
    device = relationship("Device", back_populates="metrics")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)  # device_offline, high_cpu, high_memory, network_congestion, hardware_failure
    severity = Column(String(20), nullable=False)  # critical, warning, info
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # 关系
    device = relationship("Device", back_populates="alerts")

class OptimizationLog(Base):
    __tablename__ = "optimization_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    optimization_type = Column(String(50), nullable=False)  # route_change, bandwidth_adjustment, load_balance
    old_config = Column(Text)
    new_config = Column(Text)
    reason = Column(Text)
    result = Column(String(20))  # success, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    must_change_password = Column(Boolean, default=False)  # 强制修改密码标志
    last_password_change = Column(DateTime)  # 最后修改密码时间
    failed_login_attempts = Column(Integer, default=0)  # 失败登录次数
    locked_until = Column(DateTime)  # 账户锁定时间
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)  # login, logout, device_add, device_delete, config_change, etc.
    resource_type = Column(String(50))  # device, config, user, etc.
    resource_id = Column(Integer)
    ip_address = Column(String(50))
    user_agent = Column(String(200))
    details = Column(Text)  # JSON格式的详细信息
    status = Column(String(20), default="success")  # success, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

# 初始化数据库
async def init_db():
    Base.metadata.create_all(bind=engine)
    
    # 创建默认管理员用户
    db = SessionLocal()
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=pwd_context.hash("admin123"),
                is_admin=True
            )
            db.add(admin)
            db.commit()
            print("默认管理员用户已创建: admin / admin123")
    finally:
        db.close()

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

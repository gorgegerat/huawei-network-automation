from sqlalchemy.orm import Session
from database import AuditLog, User
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import json


class AuditService:
    """审计日志服务"""
    
    @staticmethod
    def log_action(
        db: Session,
        action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ):
        """记录审计日志"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details=json.dumps(details) if details else None,
                status=status
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"审计日志记录失败: {str(e)}")
    
    @staticmethod
    def log_login(
        db: Session,
        user: User,
        ip_address: str,
        user_agent: str,
        status: str = "success"
    ):
        """记录登录日志"""
        AuditService.log_action(
            db=db,
            action="login",
            user_id=user.id,
            username=user.username,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
    
    @staticmethod
    def log_logout(
        db: Session,
        user: User,
        ip_address: str,
        user_agent: str
    ):
        """记录登出日志"""
        AuditService.log_action(
            db=db,
            action="logout",
            user_id=user.id,
            username=user.username,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_password_change(
        db: Session,
        user: User,
        ip_address: str,
        user_agent: str
    ):
        """记录密码修改日志"""
        AuditService.log_action(
            db=db,
            action="password_change",
            user_id=user.id,
            username=user.username,
            resource_type="user",
            resource_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_device_action(
        db: Session,
        user: User,
        action: str,
        device_id: int,
        ip_address: str,
        user_agent: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """记录设备操作日志"""
        AuditService.log_action(
            db=db,
            action=action,
            user_id=user.id,
            username=user.username,
            resource_type="device",
            resource_id=device_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
    
    @staticmethod
    def log_config_action(
        db: Session,
        user: User,
        action: str,
        config_id: int,
        ip_address: str,
        user_agent: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """记录配置操作日志"""
        AuditService.log_action(
            db=db,
            action=action,
            user_id=user.id,
            username=user.username,
            resource_type="config",
            resource_id=config_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

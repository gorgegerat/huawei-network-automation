import re
from typing import Optional
from fastapi import HTTPException, status


class Validators:
    """输入验证工具类"""
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """验证用户名格式"""
        if not username or len(username) < 3 or len(username) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名长度必须在3-50个字符之间"
            )
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名只能包含字母、数字和下划线"
            )
        return True
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱不能为空"
            )
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱格式不正确"
            )
        return True
    
    @staticmethod
    def validate_password(password: str) -> bool:
        """验证密码强度"""
        if not password or len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码长度至少8位"
            )
        if len(password) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码长度不能超过100位"
            )
        # 检查是否包含至少一个数字
        if not re.search(r'\d', password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码必须包含至少一个数字"
            )
        # 检查是否包含至少一个字母
        if not re.search(r'[a-zA-Z]', password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码必须包含至少一个字母"
            )
        return True
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """验证IP地址格式"""
        if not ip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="IP地址不能为空"
            )
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ip_pattern, ip):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="IP地址格式不正确"
            )
        # 检查每个段是否在0-255之间
        segments = ip.split('.')
        for segment in segments:
            if int(segment) > 255:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="IP地址格式不正确"
                )
        return True
    
    @staticmethod
    def validate_port(port: int) -> bool:
        """验证端口号"""
        if port < 1 or port > 65535:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="端口号必须在1-65535之间"
            )
        return True
    
    @staticmethod
    def validate_device_name(name: str) -> bool:
        """验证设备名称"""
        if not name or len(name) < 1 or len(name) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="设备名称长度必须在1-100个字符之间"
            )
        return True
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """清理字符串，防止XSS攻击"""
        if not input_str:
            return ""
        # 移除潜在的HTML标签
        sanitized = re.sub(r'<[^>]+>', '', input_str)
        # 限制长度
        sanitized = sanitized[:max_length]
        return sanitized.strip()

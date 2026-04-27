from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from database import get_db, User
import yaml
from pathlib import Path
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from services.audit_service import AuditService
from utils.validators import Validators
import random
import string
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# 加载配置
config_path = Path("/app/config/config.yaml")
if not config_path.exists():
    config_path = Path("../config/config.yaml")

with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

SECRET_KEY = config.get("security", {}).get("jwt_secret", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = config.get("security", {}).get("jwt_expire_hours", 24) * 60
MAX_LOGIN_ATTEMPTS = 5  # 最大登录失败次数
LOCK_DURATION_MINUTES = 30  # 账户锁定时长（分钟）

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Pydantic模型
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"密码验证错误: {e}")
        return False

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/login")
@limiter.limit("5/minute")  # 每分钟最多5次登录尝试
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # 获取客户端信息
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # 检查账户是否被锁定
    if user and user.locked_until and user.locked_until > datetime.now(timezone.utc):
        AuditService.log_login(db, user, client_ip, user_agent, "failed")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"账户已被锁定，请{int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)}分钟后重试"
        )
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        # 登录失败，增加失败次数
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCK_DURATION_MINUTES)
                db.commit()
                AuditService.log_login(db, user, client_ip, user_agent, "failed")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"登录失败次数过多，账户已被锁定{LOCK_DURATION_MINUTES}分钟"
                )
            db.commit()
            AuditService.log_login(db, user, client_ip, user_agent, "failed")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 登录成功，重置失败次数
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    
    # 记录登录审计日志
    AuditService.log_login(db, user, client_ip, user_agent, "success")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "must_change_password": user.must_change_password
        }
    }

@router.post("/register")
async def register(username: str, email: str, password: str, db: Session = Depends(get_db)):
    # 输入验证
    Validators.validate_username(username)
    Validators.validate_email(email)
    Validators.validate_password(password)
    
    # 检查用户是否已存在
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 创建新用户
    hashed_password = get_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "用户注册成功", "user_id": new_user.id}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "must_change_password": current_user.must_change_password
    }

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 验证旧密码
    if not verify_password(request.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    # 验证新密码强度
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度至少8位"
        )
    
    # 更新密码
    current_user.hashed_password = get_password_hash(request.new_password)
    current_user.must_change_password = False
    current_user.last_password_change = datetime.now(timezone.utc)
    current_user.failed_login_attempts = 0
    current_user.locked_until = None
    db.commit()
    
    return {"message": "密码修改成功"}

# 验证码存储（生产环境应使用Redis）
captcha_store = {}

def generate_captcha_text(length=4):
    """生成随机验证码"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def create_captcha_image(text):
    """创建验证码图片"""
    width, height = 120, 40
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # 添加噪点
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    
    # 添加干扰线
    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), width=1)
    
    # 绘制文字
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    for i, char in enumerate(text):
        x = 20 + i * 25
        y = random.randint(5, 15)
        draw.text((x, y), char, fill=(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100)), font=font)
    
    # 转换为base64
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

@router.get("/captcha")
async def get_captcha(request: Request):
    """获取验证码"""
    captcha_id = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    captcha_text = generate_captcha_text()
    captcha_image = create_captcha_image(captcha_text)
    
    # 存储验证码（5分钟过期）
    captcha_store[captcha_id] = {
        'text': captcha_text.lower(),
        'expires': datetime.now(timezone.utc) + timedelta(minutes=5)
    }
    
    # 清理过期验证码
    now = datetime.now(timezone.utc)
    expired_keys = [k for k, v in captcha_store.items() if v['expires'] < now]
    for k in expired_keys:
        del captcha_store[k]
    
    return {
        "captcha_id": captcha_id,
        "image": captcha_image
    }

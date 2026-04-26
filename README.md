# 华为企业网络设备自动化部署运维系统

## 系统概述

本系统实现企业网络设备（交换机、路由器、防火墙等）的自动化部署和运维，包括：
- 新设备自动从云端读取配置并部署
- 网络环境自动监控和路由优化
- 故障自动检测和修复
- 流量拥堵自动解决
- 设备软硬件故障预警
- 多渠道通知（微信、短信、邮箱）
- **ZTP零接触部署**：新设备插网线即可自动获取配置
- **多厂商设备支持**：支持华为、思科、华三等主流厂商设备
- **安全增强**：登录失败限制、审计日志、API速率限制、输入验证

## 技术栈

- **后端**: Python 3.9+ + FastAPI
- **前端**: React 18 + TypeScript + TailwindCSS
- **数据库**: SQLite
- **设备交互**: Netmiko (SSH)
- **通知**: 企业微信API、阿里云短信、SMTP
- **安全**: Passlib (密码哈希)、python-jose (JWT)、slowapi (速率限制)
- **部署**: Docker + Docker Compose

## 快速开始

### 1. 环境要求
- Docker 20.10+
- Docker Compose 2.0+
- 或 Python 3.9+ (本地开发)

### 2. 一键部署

**Windows:**
```bash
# 克隆项目
git clone https://github.com/gorgegerat/huawei-network-automation.git
cd huawei-network-automation

# 复制环境变量模板
copy .env.example .env

# 编辑 .env 文件配置（可选）
notepad .env

# 运行部署脚本
deploy.bat

# 访问前端界面
http://localhost:3000
```

**Linux/Mac:**
```bash
# 克隆项目
git clone https://github.com/gorgegerat/huawei-network-automation.git
cd huawei-network-automation

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件配置（可选）
nano .env

# 运行部署脚本
chmod +x deploy.sh
./deploy.sh

# 访问前端界面
http://localhost:3000
```

### 3. 配置说明

系统支持两种配置方式，推荐使用环境变量配置：

#### 方式一：环境变量配置（推荐）

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，根据实际情况修改配置：
```env
# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///data/network.db

# 安全配置
JWT_SECRET=your-jwt-secret-change-this-in-production

# 设备厂商配置
HUAWEI_DEFAULT_USERNAME=admin
HUAWEI_DEFAULT_PASSWORD=Admin@123
CISCO_DEFAULT_USERNAME=cisco
CISCO_DEFAULT_PASSWORD=cisco
H3C_DEFAULT_USERNAME=admin
H3C_DEFAULT_PASSWORD=admin

# 通知配置
WECHAT_CORP_ID=your-corp-id
WECHAT_AGENT_ID=your-agent-id
WECHAT_SECRET=your-secret

# ZTP配置
ZTP_DHCP_SERVER_IP=192.168.1.10
ZTP_TFTP_SERVER_IP=192.168.1.10
ZTP_HTTP_SERVER_URL=http://192.168.1.10:8080
```

**配置优先级**：环境变量 > config.yaml > 默认值

#### 方式二：配置文件配置

编辑 `config/config.yaml` 配置：
- 数据库连接
- 设备厂商SSH凭据（华为、思科、华三）
- 通知服务API密钥
- 监控阈值
- **ZTP零接触部署配置**：
  - DHCP服务器IP和端口
  - TFTP服务器端口
  - HTTP服务器端口
  - 设备发现配置
  - 配置模板目录

### 4. 需要手动配置的部分
以下配置文件需要根据实际环境修改（标有⚠️）：

**⚠️ .env 文件**（推荐）
- 复制 `.env.example` 为 `.env`
- 修改通知服务API密钥
- 修改JWT密钥（生产环境）
- 修改ZTP服务器IP地址

**⚠️ config/config.yaml**（备用）
```yaml
ztp:
  dhcp:
    server_ip: "192.168.1.10"  # 修改为实际ZTP服务器IP
    port: 67
    lease_time: 3600
  tftp:
    port: 69
    root_dir: "/tftpboot"
  http:
    port: 8080
  discovery:
    enabled: true
    scan_interval: 300
```

## 详细教程

详见 `docs/` 目录下的详细文档。

## 项目结构

```
.
├── backend/          # 后端服务
│   ├── routers/      # API路由
│   │   ├── auth.py   # 认证路由（含安全功能）
│   │   ├── devices.py # 设备管理路由
│   │   ├── configs.py # 配置管理路由
│   │   ├── monitoring.py # 监控路由
│   │   ├── alerts.py # 告警路由
│   │   ├── optimization.py # 优化路由
│   │   └── ztp.py    # ZTP路由
│   ├── services/     # 业务逻辑
│   │   ├── base_device_service.py # 设备服务基类
│   │   ├── huawei_device_service.py # 华为设备服务
│   │   ├── device_factory.py # 设备工厂
│   │   ├── audit_service.py # 审计日志服务
│   │   ├── monitor_service.py # 监控服务
│   │   ├── auto_optimization_service.py # 自动优化服务
│   │   └── notification_service.py # 通知服务
│   ├── utils/        # 工具类
│   │   └── validators.py # 输入验证
│   ├── database.py   # 数据库模型
│   ├── config_loader.py # 配置加载器
│   └── main.py       # 主程序
├── frontend/         # 前端界面
│   ├── src/
│   │   ├── pages/    # 页面组件
│   │   ├── components/ # UI组件
│   │   └── api/      # API调用
│   └── nginx.conf    # Nginx配置
├── agent/            # 设备代理
│   ├── services/     # 设备交互服务
│   └── main.py       # 主程序
├── ztp/              # ZTP零接触部署服务
│   ├── dhcp_server.py      # DHCP服务器
│   ├── tftp_server.py      # TFTP服务器
│   ├── http_server.py      # HTTP服务器
│   ├── config_template_service.py # 配置模板服务
│   ├── device_discovery.py # 设备发现服务
│   ├── main.py             # ZTP主服务
│   ├── Dockerfile          # Docker镜像
│   └── requirements.txt    # Python依赖
├── config/           # 配置文件
│   └── config.yaml   # 主配置文件（含多厂商配置）
├── docs/             # 文档
├── data/             # 数据目录（自动创建）
├── logs/             # 日志目录（自动创建）
├── tftpboot/         # TFTP根目录（自动创建）
├── ztp-templates/    # ZTP配置模板目录（自动创建）
├── docker-compose.yml
├── deploy.bat        # Windows部署脚本
├── deploy.ps1        # PowerShell部署脚本
├── stop.bat          # 停止服务脚本
├── restart.bat       # 重启服务脚本
├── logs.bat          # 查看日志脚本
├── .env.example      # 环境变量模板
└── README.md
```

## 详细部署教程

### Windows系统部署

#### 方法一：使用批处理脚本（推荐）

1. **准备环境**
   - 安装 Docker Desktop for Windows
   - 确保Docker服务正在运行

2. **运行部署脚本**
   ```bash
   # 双击运行或在命令行执行
   deploy.bat
   ```

3. **配置环境变量**
   - 脚本会自动创建 `.env` 文件（如果不存在）
   - 编辑 `.env` 文件，配置以下内容：
     ```
     SECRET_KEY=your-secret-key-change-this
     WECHAT_CORP_ID=your-wechat-corp-id
     WECHAT_CORP_SECRET=your-wechat-corp-secret
     WECHAT_AGENT_ID=your-wechat-agent-id
     ALIYUN_ACCESS_KEY=your-aliyun-access-key
     ALIYUN_ACCESS_SECRET=your-aliyun-access-secret
     ALIYUN_SMS_SIGN_NAME=your-sms-sign-name
     SMTP_HOST=smtp.example.com
     SMTP_PORT=587
     SMTP_USER=your-email@example.com
     SMTP_PASSWORD=your-email-password
     ```

4. **配置ZTP参数**
   - 编辑 `config/config.yaml`，修改ZTP配置：
     ```yaml
     ztp:
       dhcp:
         server_ip: "192.168.1.10"  # 修改为实际服务器IP
         port: 67
         lease_time: 3600
       tftp:
         port: 69
         root_dir: "/tftpboot"
       http:
         port: 8080
       discovery:
         enabled: true
         scan_interval: 300
     ```

5. **访问系统**
   - 前端界面：http://localhost:3000
   - 后端API：http://localhost:8000
   - API文档：http://localhost:8000/docs
   - ZTP HTTP服务：http://localhost:8080

#### 方法二：使用PowerShell脚本

1. **以管理员身份运行PowerShell**
   ```powershell
   # 设置执行策略
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **运行部署脚本**
   ```powershell
   .\deploy.ps1
   ```

3. **后续步骤同方法一的3-5步**

#### 方法三：手动部署

1. **创建必要目录**
   ```bash
   mkdir data
   mkdir logs
   mkdir tftpboot
   mkdir ztp-templates
   ```

2. **复制环境变量文件**
   ```bash
   copy .env.example .env
   ```

3. **编辑配置文件**
   - 编辑 `.env` 配置通知服务密钥
   - 编辑 `config/config.yaml` 配置系统参数

4. **构建Docker镜像**
   ```bash
   docker-compose build
   ```

5. **启动服务**
   ```bash
   docker-compose up -d
   ```

6. **查看服务状态**
   ```bash
   docker-compose ps
   ```

7. **查看日志**
   ```bash
   # 查看所有服务日志
   docker-compose logs -f

   # 查看特定服务日志
   docker-compose logs -f backend
   docker-compose logs -f frontend
   docker-compose logs -f agent
   docker-compose logs -f ztp
   ```

### ZTP零接触部署使用指南

#### 1. 创建配置模板

通过前端界面访问 http://localhost:3000/ztp，点击"创建模板"：

```
模板ID: core_switch
模板名称: 核心交换机配置
设备类型: switch
配置内容:
#
 sysname CoreSwitch
#
 vlan batch 10 20 30
#
 interface Vlanif10
  ip address 192.168.10.1 24
#
 interface Vlanif20
  ip address 192.168.20.1 24
#
 interface Vlanif30
  ip address 192.168.30.1 24
#
```

#### 2. 设备自动发现

1. 在ZTP页面点击"启动发现"
2. 系统会自动扫描网络中的华为设备
3. 发现的设备会显示在列表中

#### 3. 分配配置模板

1. 在发现的设备列表中，点击"分配模板"
2. 选择对应的配置模板
3. 设备会自动获取配置

#### 4. 新设备零接触部署流程

1. **物理连接**：将新华为设备连接到网络
2. **DHCP请求**：设备发送DHCP请求获取IP
3. **获取配置**：设备从TFTP/HTTP服务器下载配置
4. **应用配置**：设备自动应用配置完成部署

### 常用管理命令

```bash
# 停止所有服务
docker-compose down

# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
docker-compose restart ztp

# 查看服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f ztp

# 进入容器调试
docker exec -it network-auto-backend bash
docker exec -it network-auto-ztp bash

# 更新代码后重新构建
docker-compose up -d --build

# 清理所有容器和镜像（谨慎使用）
docker-compose down -v --rmi all
```

### 故障排查

#### 1. 端口冲突
如果端口被占用，修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "3001:3000"  # 前端改为3001
  - "8001:8000"  # 后端改为8001
```

#### 2. ZTP服务无法启动
- 检查端口69（TFTP）和8080（HTTP）是否被占用
- 确保容器有网络访问权限（privileged: true）
- 查看ZTP服务日志：`docker-compose logs -f ztp`

#### 3. 设备无法获取配置
- 确认DHCP服务器IP配置正确
- 检查网络连通性
- 查看TFTP/HTTP服务日志
- 确认配置模板已创建并分配

#### 4. 前端无法访问
- 检查前端容器是否运行：`docker-compose ps`
- 查看前端日志：`docker-compose logs -f frontend`
- 确认端口3000未被占用

### 回退到无ZTP版本

如果需要移除ZTP功能：

1. **停止并删除ZTP容器**
   ```bash
   docker-compose stop ztp
   docker-compose rm ztp
   ```

2. **修改docker-compose.yml**
   - 删除ztp服务配置块
   - 删除tftpboot和ztp-templates volumes

3. **修改backend/main.py**
   - 删除 `from routers import ... ztp`
   - 删除 `app.include_router(ztp.router, ...)`

4. **修改前端**
   - 删除 `frontend/src/pages/ZTP.tsx`
   - 从 `App.tsx` 删除ZTP路由
   - 从 `Layout.tsx` 删除ZTP导航项

5. **删除ZTP目录**
   ```bash
   rmdir /s ztp
   ```

6. **重启服务**
   ```bash
   docker-compose up -d
   ```

### 生产环境部署

生产环境部署请参考 `docs/02-生产环境部署.md`，包括：
- 使用HTTPS
- 配置防火墙
- 数据库备份
- 日志管理
- 监控告警

## 新增功能

### 安全增强

#### 1. 登录失败限制
- 连续登录失败5次后账户自动锁定30分钟
- 登录成功后自动重置失败次数
- 防止暴力破解攻击

#### 2. 强制密码修改
- 首次登录强制修改默认密码
- 密码强度验证（至少8位，包含字母和数字）
- 记录密码修改时间

#### 3. API速率限制
- 登录端点每分钟最多5次请求
- 防止API滥用和DDoS攻击
- 基于IP地址的速率限制

#### 4. 审计日志
- 记录所有用户操作（登录、登出、密码修改）
- 记录设备操作（添加、删除、配置变更）
- 记录客户端IP和User-Agent
- 支持审计追溯

#### 5. 输入验证
- 用户名格式验证（3-50字符，字母数字下划线）
- 邮箱格式验证
- 密码强度验证
- IP地址格式验证
- 防止XSS攻击

### 多厂商设备支持

#### 1. 设备服务抽象
- `BaseDeviceService` 抽象基类定义统一接口
- 所有厂商服务继承基类实现标准方法
- 支持扩展新厂商设备

#### 2. 设备工厂模式
- `DeviceFactory` 根据厂商动态创建服务实例
- 支持运行时注册新厂商服务
- 当前支持：华为、思科、华三

#### 3. 配置文件扩展
- `config.yaml` 新增 `vendors` 配置段
- 每个厂商独立配置默认凭据和参数
- 支持设备类型映射

#### 4. 扩展示例
添加新厂商设备支持：
```python
# 1. 创建厂商服务类
class CiscoDeviceService(BaseDeviceService):
    def __init__(self):
        super().__init__()
        self.vendor = "cisco"
    
    async def connect(self, device: Device) -> Dict[str, Any]:
        # 实现连接逻辑
        pass
    
    # 实现其他抽象方法...

# 2. 注册到设备工厂
DeviceFactory.register_service('cisco', CiscoDeviceService)

# 3. 在config.yaml添加配置
vendors:
  cisco:
    default_username: "cisco"
    default_password: "cisco"
    device_type: "cisco_ios"
```

### 健康检查

#### 1. 健康检查端点
- `GET /health` - 系统健康状态
- 返回数据库连接状态
- 返回监控服务运行状态
- 返回自动优化服务运行状态

#### 2. 根端点
- `GET /` - 系统基本信息
- 返回系统版本
- 返回API文档链接

## API端点

### 认证相关
- `POST /api/auth/login` - 用户登录（含速率限制）
- `POST /api/auth/register` - 用户注册（含输入验证）
- `POST /api/auth/change-password` - 修改密码
- `GET /api/auth/me` - 获取当前用户信息

### 健康检查
- `GET /health` - 健康检查
- `GET /` - 根端点

### 其他端点
详见 `http://localhost:8000/docs` (Swagger UI)

## 默认登录凭据

- 用户名: `admin`
- 密码: `admin123`

**注意：** 首次登录后系统会提示修改默认密码。

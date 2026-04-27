# 华为企业网络设备自动化部署运维系统

企业网络设备（交换机、路由器、防火墙）的自动化部署和运维系统，支持多厂商设备，提供零接触部署、自动监控、故障检测等功能。

## 核心功能

- **ZTP零接触部署**：新设备插网线即可自动获取配置
- **多厂商支持**：华为、思科、华三等主流厂商设备
- **自动监控**：网络环境监控和路由优化
- **故障检测**：自动检测和修复网络故障
- **安全增强**：登录限制、审计日志、API速率限制
- **多渠道通知**：企业微信、短信、邮箱告警

## 技术栈

- **后端**：Python 3.9+ + FastAPI
- **前端**：React 18 + TypeScript + TailwindCSS
- **数据库**：SQLite
- **部署**：Docker + Docker Compose

## 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 2.0+

### 一键部署

**Windows:**
```bash
git clone https://github.com/gorgegerat/huawei-network-automation.git
cd huawei-network-automation
copy .env.example .env
deploy.bat
```

**Linux/Mac:**
```bash
git clone https://github.com/gorgegerat/huawei-network-automation.git
cd huawei-network-automation
cp .env.example .env
chmod +x deploy.sh
./deploy.sh
```

### 访问系统

- 前端界面：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

### 默认登录

- 用户名：`admin`
- 密码：`admin123`

## 配置说明

### 环境变量配置（推荐）

复制 `.env.example` 为 `.env`，修改以下配置：

```env
# 安全配置
JWT_SECRET=your-jwt-secret-change-this-in-production

# 设备厂商配置
HUAWEI_DEFAULT_USERNAME=admin
HUAWEI_DEFAULT_PASSWORD=Admin@123

# 通知配置
WECHAT_CORP_ID=your-corp-id
WECHAT_AGENT_ID=your-agent-id
WECHAT_SECRET=your-secret

# ZTP配置
ZTP_DHCP_SERVER_IP=192.168.1.10
ZTP_TFTP_SERVER_IP=192.168.1.10
ZTP_HTTP_SERVER_URL=http://192.168.1.10:8080
```

### 配置文件配置

编辑 `config/config.yaml` 配置：
- 数据库连接
- 设备厂商SSH凭据
- 通知服务API密钥
- 监控阈值
- ZTP服务器配置

## 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f ztp

# 重新构建
docker-compose up -d --build
```

## ZTP零接触部署

### 使用流程

1. **创建配置模板**：在前端ZTP页面创建设备配置模板
2. **设备发现**：系统自动扫描网络中的设备
3. **分配模板**：为发现的设备分配配置模板
4. **自动部署**：新设备连接网络后自动获取配置

### 配置示例

```
模板ID: core_switch
模板名称: 核心交换机配置
设备类型: switch
配置内容:
 sysname CoreSwitch
 vlan batch 10 20 30
 interface Vlanif10
  ip address 192.168.10.1 24
```

## 项目结构

```
.
├── backend/          # 后端服务
│   ├── routers/      # API路由
│   ├── services/     # 业务逻辑
│   ├── utils/        # 工具类
│   └── main.py       # 主程序
├── frontend/         # 前端界面
│   ├── src/
│   │   ├── pages/    # 页面组件
│   │   ├── components/ # UI组件
│   │   └── api/      # API调用
│   └── nginx.conf    # Nginx配置
├── agent/            # 设备代理
├── ztp/              # ZTP零接触部署服务
├── config/           # 配置文件
├── docker-compose.yml
└── README.md
```

## 故障排查

### 端口冲突

修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "3001:3000"  # 前端改为3001
  - "8001:8000"  # 后端改为8001
```

### ZTP服务无法启动

- 检查端口69（TFTP）和8080（HTTP）是否被占用
- 查看ZTP服务日志：`docker-compose logs -f ztp`

### 前端无法访问

- 检查前端容器是否运行：`docker-compose ps`
- 查看前端日志：`docker-compose logs -f frontend`

## 安全功能

- **登录失败限制**：连续失败5次锁定30分钟
- **密码强度验证**：至少8位，包含字母和数字
- **API速率限制**：防止API滥用
- **审计日志**：记录所有用户操作
- **输入验证**：防止XSS攻击

## 详细文档

详见 `docs/` 目录下的详细文档。

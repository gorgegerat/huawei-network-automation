# API 文档

## 基础信息

- **Base URL**: `http://localhost:8000/api`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

## 认证

### 登录

获取访问令牌。

**请求**
```
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**响应**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com"
  }
}
```

### 获取当前用户信息

**请求**
```
GET /auth/me
Authorization: Bearer <token>
```

**响应**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 登出

**请求**
```
POST /auth/logout
Authorization: Bearer <token>
```

**响应**
```json
{
  "message": "Successfully logged out"
}
```

## 设备管理

### 获取设备列表

**请求**
```
GET /devices
Authorization: Bearer <token>
```

**查询参数**
- `page`: 页码（默认 1）
- `limit`: 每页数量（默认 20）
- `search`: 搜索关键词
- `status`: 状态过滤（online/offline）

**响应**
```json
{
  "total": 10,
  "page": 1,
  "limit": 20,
  "items": [
    {
      "id": 1,
      "name": "核心交换机-01",
      "ip": "192.168.1.1",
      "port": 22,
      "device_type": "switch",
      "status": "online",
      "last_connected": "2024-01-01T12:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 获取设备详情

**请求**
```
GET /devices/{device_id}
Authorization: Bearer <token>
```

**响应**
```json
{
  "id": 1,
  "name": "核心交换机-01",
  "ip": "192.168.1.1",
  "port": 22,
  "username": "admin",
  "device_type": "switch",
  "status": "online",
  "description": "核心交换机",
  "system_info": {
    "hostname": "Core-Switch-01",
    "version": "VRP V200R021C00",
    "serial": "1234567890"
  },
  "interfaces": [
    {
      "name": "GigabitEthernet0/0/1",
      "status": "up",
      "description": "Uplink to Core"
    }
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### 创建设备

**请求**
```
POST /devices
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "核心交换机-01",
  "ip": "192.168.1.1",
  "port": 22,
  "username": "admin",
  "password": "Admin@123",
  "device_type": "switch",
  "description": "核心交换机"
}
```

**响应**
```json
{
  "id": 1,
  "name": "核心交换机-01",
  "ip": "192.168.1.1",
  "port": 22,
  "device_type": "switch",
  "status": "offline",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 更新设备

**请求**
```
PUT /devices/{device_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "核心交换机-01",
  "description": "更新后的描述"
}
```

**响应**
```json
{
  "id": 1,
  "name": "核心交换机-01",
  "description": "更新后的描述",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### 删除设备

**请求**
```
DELETE /devices/{device_id}
Authorization: Bearer <token>
```

**响应**
```json
{
  "message": "Device deleted successfully"
}
```

### 连接设备

**请求**
```
POST /devices/{device_id}/connect
Authorization: Bearer <token>
```

**响应**
```json
{
  "status": "online",
  "message": "Device connected successfully"
}
```

### 断开设备

**请求**
```
POST /devices/{device_id}/disconnect
Authorization: Bearer <token>
```

**响应**
```json
{
  "status": "offline",
  "message": "Device disconnected successfully"
}
```

## 配置管理

### 获取配置列表

**请求**
```
GET /configs?device_id={device_id}
Authorization: Bearer <token>
```

**响应**
```json
{
  "total": 5,
  "items": [
    {
      "id": 1,
      "device_id": 1,
      "name": "接口配置",
      "type": "interface",
      "content": "interface GigabitEthernet0/0/1\n...",
      "status": "draft",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 创建配置

**请求**
```
POST /configs
Authorization: Bearer <token>
Content-Type: application/json

{
  "device_id": 1,
  "name": "接口配置",
  "type": "interface",
  "content": "interface GigabitEthernet0/0/1\n description Uplink",
  "description": "上行接口配置"
}
```

**响应**
```json
{
  "id": 1,
  "device_id": 1,
  "name": "接口配置",
  "type": "interface",
  "status": "draft",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 更新配置

**请求**
```
PUT /configs/{config_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "interface GigabitEthernet0/0/1\n description Updated"
}
```

**响应**
```json
{
  "id": 1,
  "content": "interface GigabitEthernet0/0/1\n description Updated",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### 删除配置

**请求**
```
DELETE /configs/{config_id}
Authorization: Bearer <token>
```

**响应**
```json
{
  "message": "Config deleted successfully"
}
```

### 激活配置

**请求**
```
POST /configs/{config_id}/activate
Authorization: Bearer <token>
```

**响应**
```json
{
  "status": "activated",
  "message": "Config activated successfully"
}
```

### 部署配置

**请求**
```
POST /configs/{config_id}/deploy
Authorization: Bearer <token>
```

**响应**
```json
{
  "status": "deployed",
  "message": "Config deployed successfully",
  "result": {
    "success": true,
    "output": "Configuration applied successfully"
  }
}
```

## 监控数据

### 获取设备监控数据

**请求**
```
GET /monitoring/{device_id}
Authorization: Bearer <token>
```

**查询参数**
- `start_time`: 开始时间（ISO 8601 格式）
- `end_time`: 结束时间（ISO 8601 格式）

**响应**
```json
{
  "device_id": 1,
  "metrics": {
    "cpu": {
      "current": 45.5,
      "history": [
        {"time": "2024-01-01T10:00:00Z", "value": 40.2},
        {"time": "2024-01-01T10:05:00Z", "value": 45.5}
      ]
    },
    "memory": {
      "current": 65.3,
      "history": [...]
    },
    "bandwidth": {
      "inbound": 500.5,
      "outbound": 300.2,
      "history": [...]
    },
    "latency": {
      "current": 12.5,
      "history": [...]
    },
    "packet_loss": {
      "current": 0.1,
      "history": [...]
    }
  }
}
```

### 获取所有设备概览

**请求**
```
GET /monitoring/overview
Authorization: Bearer <token>
```

**响应**
```json
{
  "total_devices": 10,
  "online_devices": 8,
  "offline_devices": 2,
  "alerts_count": 5,
  "devices": [
    {
      "id": 1,
      "name": "核心交换机-01",
      "status": "online",
      "cpu": 45.5,
      "memory": 65.3
    }
  ]
}
```

## 告警管理

### 获取告警列表

**请求**
```
GET /alerts
Authorization: Bearer <token>
```

**查询参数**
- `page`: 页码
- `limit`: 每页数量
- `severity`: 严重级别（critical/warning/info）
- `status`: 状态（unresolved/resolved）
- `device_id`: 设备 ID

**响应**
```json
{
  "total": 10,
  "items": [
    {
      "id": 1,
      "device_id": 1,
      "device_name": "核心交换机-01",
      "severity": "critical",
      "type": "high_cpu",
      "message": "CPU usage exceeds threshold",
      "status": "unresolved",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### 获取告警详情

**请求**
```
GET /alerts/{alert_id}
Authorization: Bearer <token>
```

**响应**
```json
{
  "id": 1,
  "device_id": 1,
  "device_name": "核心交换机-01",
  "severity": "critical",
  "type": "high_cpu",
  "message": "CPU usage exceeds threshold",
  "details": {
    "current_value": 85.5,
    "threshold": 80
  },
  "status": "unresolved",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### 处理告警

**请求**
```
POST /alerts/{alert_id}/resolve
Authorization: Bearer <token>
Content-Type: application/json

{
  "note": "已重启相关服务"
}
```

**响应**
```json
{
  "id": 1,
  "status": "resolved",
  "resolved_at": "2024-01-01T12:30:00Z",
  "note": "已重启相关服务"
}
```

## 优化管理

### 获取优化状态

**请求**
```
GET /optimization/status
Authorization: Bearer <token>
```

**响应**
```json
{
  "auto_optimization": true,
  "last_optimization": "2024-01-01T10:00:00Z",
  "enabled_features": {
    "route_optimization": true,
    "bandwidth_management": true,
    "load_balancing": true
  }
}
```

### 手动触发优化

**请求**
```
POST /optimization/trigger
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "route",
  "device_id": 1
}
```

**响应**
```json
{
  "status": "running",
  "optimization_id": "opt_123456",
  "message": "Optimization started"
}
```

### 获取优化日志

**请求**
```
GET /optimization/logs
Authorization: Bearer <token>
```

**查询参数**
- `page`: 页码
- `limit`: 每页数量
- `device_id`: 设备 ID

**响应**
```json
{
  "total": 20,
  "items": [
    {
      "id": 1,
      "device_id": 1,
      "device_name": "核心交换机-01",
      "type": "route",
      "status": "success",
      "message": "Route optimization completed",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

## 错误响应

所有错误响应遵循以下格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": {}
  }
}
```

### 常见错误码

- `INVALID_CREDENTIALS`: 用户名或密码错误
- `UNAUTHORIZED`: 未授权访问
- `DEVICE_NOT_FOUND`: 设备不存在
- `DEVICE_OFFLINE`: 设备离线
- `CONFIG_NOT_FOUND`: 配置不存在
- `DEPLOYMENT_FAILED`: 配置部署失败
- `VALIDATION_ERROR`: 请求参数验证失败

### 示例错误响应

```json
{
  "error": {
    "code": "DEVICE_OFFLINE",
    "message": "Device is currently offline",
    "details": {
      "device_id": 1,
      "device_name": "核心交换机-01"
    }
  }
}
```

## 速率限制

API 请求速率限制为每分钟 100 次。

超过限制时返回：
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded"
  }
}
```

## WebSocket

系统支持 WebSocket 实时推送：

### 连接

```
ws://localhost:8000/ws
```

### 认证

在连接 URL 中添加 token：
```
ws://localhost:8000/ws?token=<access_token>
```

### 消息格式

**告警推送**
```json
{
  "type": "alert",
  "data": {
    "id": 1,
    "severity": "critical",
    "message": "CPU usage exceeds threshold"
  }
}
```

**监控数据推送**
```json
{
  "type": "monitoring",
  "data": {
    "device_id": 1,
    "cpu": 45.5,
    "memory": 65.3
  }
}
```

## 交互式 API 文档

访问 http://localhost:8000/docs 查看交互式 API 文档（Swagger UI）。

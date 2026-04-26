# 华为网络自动化运维系统 - PowerShell部署脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "华为网络自动化运维系统 - 部署脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Docker
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker未安装"
    }
    Write-Host "[1/5] 检查Docker环境... 完成" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未检测到Docker，请先安装Docker Desktop" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 检查Docker Compose
try {
    $composeVersion = docker-compose --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose未安装"
    }
    Write-Host "[2/5] 检查Docker Compose... 完成" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未检测到Docker Compose，请先安装Docker Compose" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""

# 创建必要的目录
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
}
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}
if (-not (Test-Path "tftpboot")) {
    New-Item -ItemType Directory -Path "tftpboot" | Out-Null
}
if (-not (Test-Path "ztp-templates")) {
    New-Item -ItemType Directory -Path "ztp-templates" | Out-Null
}
Write-Host "[3/5] 创建数据目录... 完成" -ForegroundColor Green
Write-Host ""

# 复制环境变量配置
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "[4/5] 创建环境变量文件... 完成" -ForegroundColor Green
        Write-Host "[提示] 请编辑 .env 文件配置您的API密钥和凭据" -ForegroundColor Yellow
    } else {
        Write-Host "[警告] 未找到 .env.example 文件" -ForegroundColor Yellow
    }
} else {
    Write-Host "[4/5] 环境变量文件已存在... 跳过" -ForegroundColor Green
}
Write-Host ""

# 构建镜像
Write-Host "[5/5] 构建Docker镜像..." -ForegroundColor Cyan
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 镜像构建失败" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}
Write-Host "镜像构建完成" -ForegroundColor Green
Write-Host ""

# 启动服务
Write-Host "启动服务..." -ForegroundColor Cyan
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 服务启动失败" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}
Write-Host "服务启动完成" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "前端访问地址: http://localhost:3000" -ForegroundColor White
Write-Host "后端API地址: http://localhost:8000" -ForegroundColor White
Write-Host "API文档地址: http://localhost:8000/docs" -ForegroundColor White
Write-Host "ZTP HTTP服务: http://localhost:8080" -ForegroundColor White
Write-Host "ZTP TFTP服务: tftp://localhost:69" -ForegroundColor White
Write-Host ""
Write-Host "常用命令:" -ForegroundColor Cyan
Write-Host "  查看日志: docker-compose logs -f" -ForegroundColor Gray
Write-Host "  停止服务: docker-compose down" -ForegroundColor Gray
Write-Host "  重启服务: docker-compose restart" -ForegroundColor Gray
Write-Host ""

Read-Host "按回车键退出"

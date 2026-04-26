@echo off
chcp 65001 >nul
echo ========================================
echo 华为网络自动化运维系统 - 部署脚本
echo ========================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Docker，请先安装Docker Desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Docker Compose，请先安装Docker Compose
    pause
    exit /b 1
)

echo [1/5] 检查Docker环境... 完成
echo.

REM 创建必要的目录
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "tftpboot" mkdir tftpboot
if not exist "ztp-templates" mkdir ztp-templates
echo [2/5] 创建数据目录... 完成
echo.

REM 复制环境变量配置
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [3/5] 创建环境变量文件... 完成
        echo [提示] 请编辑 .env 文件配置您的API密钥和凭据
    ) else (
        echo [警告] 未找到 .env.example 文件
    )
) else (
    echo [3/5] 环境变量文件已存在... 跳过
)
echo.

REM 构建镜像
echo [4/5] 构建Docker镜像...
docker-compose build
if %errorlevel% neq 0 (
    echo [错误] 镜像构建失败
    pause
    exit /b 1
)
echo 镜像构建完成
echo.

REM 启动服务
echo [5/5] 启动服务...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [错误] 服务启动失败
    pause
    exit /b 1
)
echo 服务启动完成
echo.

echo ========================================
echo 部署完成！
echo ========================================
echo.
echo 前端访问地址: http://localhost:3000
echo 后端API地址: http://localhost:8000
echo API文档地址: http://localhost:8000/docs
echo ZTP HTTP服务: http://localhost:8080
echo ZTP TFTP服务: tftp://localhost:69
echo.
echo 常用命令:
echo   查看日志: docker-compose logs -f
echo   停止服务: docker-compose down
echo   重启服务: docker-compose restart
echo.
pause

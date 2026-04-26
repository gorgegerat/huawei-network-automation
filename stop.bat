@echo off
chcp 65001 >nul
echo ========================================
echo 停止华为网络自动化运维系统
echo ========================================
echo.

docker-compose down

if %errorlevel% equ 0 (
    echo 服务已停止
) else (
    echo [错误] 停止服务失败
)

echo.
pause

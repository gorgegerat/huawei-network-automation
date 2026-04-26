@echo off
chcp 65001 >nul
echo ========================================
echo 重启华为网络自动化运维系统
echo ========================================
echo.

docker-compose restart

if %errorlevel% equ 0 (
    echo 服务已重启
) else (
    echo [错误] 重启服务失败
)

echo.
pause

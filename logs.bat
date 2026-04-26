@echo off
chcp 65001 >nul
echo ========================================
echo 查看华为网络自动化运维系统日志
echo ========================================
echo.
echo 按 Ctrl+C 退出日志查看
echo.

docker-compose logs -f

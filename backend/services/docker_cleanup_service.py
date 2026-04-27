#!/usr/bin/env python3
"""
Docker缓存清理服务
定期清理未使用的Docker资源
"""

import subprocess
import logging
from datetime import datetime, timezone
from typing import Dict, Any
import asyncio

logger = logging.getLogger(__name__)


class DockerCleanupService:
    """Docker缓存清理服务"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("docker_cleanup", {}).get("enabled", True)
        self.schedule_hours = config.get("docker_cleanup", {}).get("schedule_hours", 24)
        self.keep_images = config.get("docker_cleanup", {}).get("keep_images", 3)
        self.keep_containers = config.get("docker_cleanup", {}).get("keep_containers", 5)
        self.last_cleanup = None

    async def cleanup_unused_images(self) -> Dict[str, Any]:
        """清理未使用的Docker镜像"""
        try:
            logger.info("开始清理未使用的Docker镜像")
            
            # 获取所有镜像
            result = subprocess.run(
                ["docker", "images", "--format", "{{.ID}}"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"获取Docker镜像失败: {result.stderr}")
                return {"success": False, "error": result.stderr}
            
            image_ids = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # 清理dangling镜像
            dangling_result = subprocess.run(
                ["docker", "image", "prune", "-f"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            reclaimed_space = 0
            if dangling_result.returncode == 0:
                logger.info(f"清理dangling镜像成功: {dangling_result.stdout}")
                # 尝试解析回收的空间
                if "Total reclaimed space:" in dangling_result.stdout:
                    try:
                        space_str = dangling_result.stdout.split("Total reclaimed space:")[1].strip()
                        reclaimed_space = self._parse_space(space_str)
                    except:
                        pass
            
            return {
                "success": True,
                "reclaimed_space": reclaimed_space,
                "message": f"清理完成，回收空间: {reclaimed_space}MB"
            }
            
        except subprocess.TimeoutExpired:
            logger.error("清理Docker镜像超时")
            return {"success": False, "error": "操作超时"}
        except Exception as e:
            logger.error(f"清理Docker镜像失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def cleanup_unused_containers(self) -> Dict[str, Any]:
        """清理未使用的Docker容器"""
        try:
            logger.info("开始清理未使用的Docker容器")
            
            # 清理已停止的容器
            result = subprocess.run(
                ["docker", "container", "prune", "-f"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"清理Docker容器失败: {result.stderr}")
                return {"success": False, "error": result.stderr}
            
            removed_count = 0
            if "Total reclaimed space:" in result.stdout:
                logger.info(f"清理容器成功: {result.stdout}")
                # 尝试解析删除的容器数量
                if "containers deleted:" in result.stdout.lower():
                    try:
                        count_str = result.stdout.lower().split("containers deleted:")[1].strip().split()[0]
                        removed_count = int(count_str)
                    except:
                        pass
            
            return {
                "success": True,
                "removed_count": removed_count,
                "message": f"清理完成，删除容器: {removed_count}个"
            }
            
        except subprocess.TimeoutExpired:
            logger.error("清理Docker容器超时")
            return {"success": False, "error": "操作超时"}
        except Exception as e:
            logger.error(f"清理Docker容器失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def cleanup_unused_volumes(self) -> Dict[str, Any]:
        """清理未使用的Docker卷"""
        try:
            logger.info("开始清理未使用的Docker卷")
            
            result = subprocess.run(
                ["docker", "volume", "prune", "-f"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"清理Docker卷失败: {result.stderr}")
                return {"success": False, "error": result.stderr}
            
            reclaimed_space = 0
            if "Total reclaimed space:" in result.stdout:
                logger.info(f"清理卷成功: {result.stdout}")
                try:
                    space_str = result.stdout.split("Total reclaimed space:")[1].strip()
                    reclaimed_space = self._parse_space(space_str)
                except:
                    pass
            
            return {
                "success": True,
                "reclaimed_space": reclaimed_space,
                "message": f"清理完成，回收空间: {reclaimed_space}MB"
            }
            
        except subprocess.TimeoutExpired:
            logger.error("清理Docker卷超时")
            return {"success": False, "error": "操作超时"}
        except Exception as e:
            logger.error(f"清理Docker卷失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def cleanup_build_cache(self) -> Dict[str, Any]:
        """清理Docker构建缓存"""
        try:
            logger.info("开始清理Docker构建缓存")
            
            result = subprocess.run(
                ["docker", "builder", "prune", "-f"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"清理Docker构建缓存失败: {result.stderr}")
                return {"success": False, "error": result.stderr}
            
            reclaimed_space = 0
            if "Total reclaimed space:" in result.stdout:
                logger.info(f"清理构建缓存成功: {result.stdout}")
                try:
                    space_str = result.stdout.split("Total reclaimed space:")[1].strip()
                    reclaimed_space = self._parse_space(space_str)
                except:
                    pass
            
            return {
                "success": True,
                "reclaimed_space": reclaimed_space,
                "message": f"清理完成，回收空间: {reclaimed_space}MB"
            }
            
        except subprocess.TimeoutExpired:
            logger.error("清理Docker构建缓存超时")
            return {"success": False, "error": "操作超时"}
        except Exception as e:
            logger.error(f"清理Docker构建缓存失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def full_cleanup(self) -> Dict[str, Any]:
        """执行完整的Docker清理"""
        if not self.enabled:
            logger.info("Docker清理服务未启用")
            return {"success": True, "message": "服务未启用"}
        
        logger.info("开始执行完整的Docker清理")
        start_time = datetime.now(timezone.utc)
        
        results = {
            "images": await self.cleanup_unused_images(),
            "containers": await self.cleanup_unused_containers(),
            "volumes": await self.cleanup_unused_volumes(),
            "build_cache": await self.cleanup_build_cache()
        }
        
        total_reclaimed = sum(
            r.get("reclaimed_space", 0) for r in results.values() if r.get("success")
        )
        
        self.last_cleanup = datetime.now(timezone.utc)
        
        summary = {
            "success": all(r.get("success", False) for r in results.values()),
            "start_time": start_time,
            "end_time": datetime.now(timezone.utc),
            "total_reclaimed_space_mb": total_reclaimed,
            "details": results
        }
        
        logger.info(f"Docker清理完成，总回收空间: {total_reclaimed}MB")
        return summary

    def _parse_space(self, space_str: str) -> float:
        """解析空间字符串为MB"""
        try:
            space_str = space_str.strip()
            if space_str.endswith("GB"):
                return float(space_str[:-2]) * 1024
            elif space_str.endswith("MB"):
                return float(space_str[:-2])
            elif space_str.endswith("KB"):
                return float(space_str[:-2]) / 1024
            elif space_str.endswith("B"):
                return float(space_str[:-1]) / (1024 * 1024)
            return float(space_str)
        except:
            return 0

    def get_status(self) -> Dict[str, Any]:
        """获取清理服务状态"""
        return {
            "enabled": self.enabled,
            "schedule_hours": self.schedule_hours,
            "last_cleanup": self.last_cleanup,
            "keep_images": self.keep_images,
            "keep_containers": self.keep_containers
        }

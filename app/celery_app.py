"""Celery 应用入口（供 worker 命令行启动）"""
from .tasks import celery_app

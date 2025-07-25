from celery import Celery
import os
from kombu import Queue

# Redis配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 创建Celery应用
celery_app = Celery(
    "app", broker=REDIS_URL, backend=REDIS_URL
)

# 基本Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # 添加Redis连接配置
    broker_connection_retry_on_startup=True,
    broker_transport_options={'visibility_timeout': 3600},
    result_expires=3600,
    # 工作进程配置 - 使用solo pool解决Python 3.13兼容性问题
    worker_pool='solo',
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    # 任务路由配置
    task_routes={
        'app.tasks.download_video_task': {'queue': 'download'},
        'app.tasks.get_video_info_task': {'queue': 'download'},
        'app.tasks.cleanup_task': {'queue': 'maintenance'},
        'app.tasks.health_check_task': {'queue': 'default'},
    },
    # 队列配置
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'exchange_type': 'direct',
            'routing_key': 'default'
        },
        'download': {
            'exchange': 'download',
            'exchange_type': 'direct',
            'routing_key': 'download'
        },
        'maintenance': {
            'exchange': 'maintenance',
            'exchange_type': 'direct',
            'routing_key': 'maintenance'
        }
    },
)

# 任务发现
celery_app.autodiscover_tasks(["app"])

# 显式导入任务模块确保注册
from . import tasks


@celery_app.task(bind=True)
def debug_task(self):
    """调试任务"""
    print(f"Request: {self.request!r}")
    return "Debug task completed"


if __name__ == "__main__":
    celery_app.start()

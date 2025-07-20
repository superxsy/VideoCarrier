from celery import Celery
import os
from kombu import Queue

# Redis配置
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# 创建Celery应用
celery_app = Celery(
    'youtube_downloader',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks']
)

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # 任务路由
    task_routes={
        'app.tasks.download_video_task': {'queue': 'download'},
        'app.tasks.cleanup_task': {'queue': 'maintenance'},
    },
    
    # 队列配置
    task_default_queue='default',
    task_queues=(
        Queue('default', routing_key='default'),
        Queue('download', routing_key='download'),
        Queue('maintenance', routing_key='maintenance'),
    ),
    
    # 工作进程配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # 任务超时设置
    task_soft_time_limit=1800,  # 30分钟软超时
    task_time_limit=2400,       # 40分钟硬超时
    
    # 结果过期时间
    result_expires=3600,        # 1小时
    
    # 任务重试配置
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # 日志配置
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# 任务发现
celery_app.autodiscover_tasks(['app'])

@celery_app.task(bind=True)
def debug_task(self):
    """调试任务"""
    print(f'Request: {self.request!r}')
    return 'Debug task completed'

if __name__ == '__main__':
    celery_app.start()
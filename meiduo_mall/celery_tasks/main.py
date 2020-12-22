"""
xtbo97
"""
from celery import Celery

# 创建Celery对象
celery_app = Celery('demo')

# 加载配置信息
celery_app.config_from_object('celery_tasks.config')

# 找任务
celery_app.autodiscover_tasks(['celery_tasks.sms'])

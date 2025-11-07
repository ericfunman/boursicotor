"""
Celery configuration for asynchronous data collection tasks
"""
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_DB = os.getenv('REDIS_DB', '0')
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

# Create Celery app
celery_app = Celery(
    'boursicotor',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['backend.tasks', 'backend.live_data_task']
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    
    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours
    result_persistent=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Only fetch one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    
    # Retry settings
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,
)

# Optional: Beat scheduler for periodic tasks (future use)
celery_app.conf.beat_schedule = {
    # Example: Daily data update at 19:00
    # 'update-all-tickers': {
    #     'task': 'backend.tasks.update_all_tickers',
    #     'schedule': crontab(hour=19, minute=0),
    # },
}

if __name__ == '__main__':
    celery_app.start()

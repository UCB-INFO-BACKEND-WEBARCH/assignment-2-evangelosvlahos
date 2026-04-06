import os
import time
import logging

import redis
from rq.decorators import job

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_conn = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

@job('notifications', connection=redis_conn)
def send_due_date_reminder(task_title):
    """
    Background job to send a due date reminder notification.

    This job simulates sending a notification by waiting 5 seconds
    and then logging a reminder message.

    Args:
        task_title (str): The title of the task that's due soon
    """

    # Simulate sending notification (wait 5 seconds)
    time.sleep(5)

    # Log the reminder message
    logger.info(f"Reminder: Task '{task_title}' is due soon!")

    return f"Reminder sent for task: {task_title}"
import os
from dotenv import load_dotenv
import redis
from rq import Worker, Queue, Connection

load_dotenv()

# Redis connection
redis_conn = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
queue = Queue('notifications', connection=redis_conn)


if __name__ == '__main__':
    with Connection(redis_conn):
        worker = Worker()
        worker.work()

# Check if we should queue a notification

# def check_and_queue_notification(task):
#     # Schedule reminder if due_date is provided
#     serialized_task = task_schema.dump(task)
#     notification_queued = False
#     if task.due_date:
#         now = datetime.now(task.due_date.tzinfo) if task.due_date.tzinfo else datetime.now()
#         time_until_due = task.due_date - now

#         # Queue notification if due date is in the future and within 24 hours
#         if time_until_due > timedelta(0) and time_until_due <= timedelta(hours=24):
#             try:
#                 # Connect to Redis and queue the job
#                 redis_conn = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
#                 queue = Queue(connection=redis_conn)
#                 queue.enqueue(send_due_date_reminder, task.title)
#                 notification_queued = True
#             except Exception as e:
#                 # Log the error but don't fail the task creation
#                 print(f"Failed to queue notification: {e}")

#     # Return task data with notification status
#     response_data = {
#         "task": serialized_task,
#         "notification_queued": notification_queued
#     }
#     return jsonify(response_data), 201
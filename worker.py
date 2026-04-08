import os
from dotenv import load_dotenv
import redis
from rq import Worker, Queue, Connection

load_dotenv()

# Redis connection
redis_conn = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
queue = Queue('notifications', connection=redis_conn)

# Process jobs from the 'notifications' queue
if __name__ == '__main__':
    with Connection(redis_conn):
        worker = Worker()
        worker.work()

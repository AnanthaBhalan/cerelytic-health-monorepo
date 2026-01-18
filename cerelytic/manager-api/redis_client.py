import redis
import json
import os
from dotenv import load_dotenv
from uuid import uuid4
from datetime import datetime

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Single queue name (assignment requirement)
QUEUE_NAME = os.getenv("QUEUE_NAME", "bill-analysis-jobs")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def enqueue_analysis_job(bill_id: int, user_id: str) -> bool:
    """Enqueue an analysis job to Redis"""

    job_payload = {
        "job_id": str(uuid4()),
        "bill_id": bill_id,
        "user_id": user_id,
        "attempt": 1,
        "created_at": datetime.utcnow().isoformat()
    }

    try:
        redis_client.lpush(QUEUE_NAME, json.dumps(job_payload))
        return True
    except Exception as e:
        print(f"Failed to enqueue job: {e}")
        return False


def dequeue_analysis_job() -> dict | None:
    """Dequeue an analysis job from Redis (blocking)"""

    try:
        result = redis_client.brpop(QUEUE_NAME, timeout=30)
        if result:
            _, job_data = result
            return json.loads(job_data)
        return None
    except Exception as e:
        print(f"Failed to dequeue job: {e}")
        return None

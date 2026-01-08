import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def dequeue_analysis_job() -> dict:
    """Dequeue an analysis job from Redis (blocking)"""
    try:
        result = redis_client.brpop("analysis_jobs", timeout=30)
        if result:
            _, job_data = result
            return json.loads(job_data)
        return None
    except Exception as e:
        print(f"Failed to dequeue job: {e}")
        return None

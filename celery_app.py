import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_SSL = os.getenv("REDIS_SSL", "false").lower() == "true"

REDIS_SCHEME = "rediss" if REDIS_SSL else "redis"
REDIS_CERT = "?ssl_cert_reqs=none" if REDIS_SSL else "" 
REDIS_URL = (
    f"{REDIS_SCHEME}://{REDIS_HOST}:{REDIS_PORT}/0"
    f"{REDIS_CERT}"
)

celery = Celery(
    "emotion_api",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery.conf.update(
    imports=("tasks",)
)
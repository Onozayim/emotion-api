import redis_client

from dotenv import load_dotenv
import os

load_dotenv()

redis_client = redis_client.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    ssl=True,
    decode_responses=True
)
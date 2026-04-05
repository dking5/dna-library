import os
import redis.asyncio as redis
from typing import Optional

class RedisManager:
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")        

    async def connect(self):
        if not self.client:
            self.client = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
            try:
                await self.client.ping()
                print("DEBUG: Connected to Redis successfully!")
            except redis.ConnectionError as e:
                print(f"DEBUG: Failed to connect to Redis: {e}")
                self.client = None

    async def disconnect(self):
        if self.client:
            await self.client.close()
            print("DEBUG: Redis connection closed gracefully.")

redis_manager = RedisManager()
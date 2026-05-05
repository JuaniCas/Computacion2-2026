import redis
import time
import os

r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379)
print("Worker iniciado. Sumando visitas...")

while True:
    try:
        r.incr('contador_global')
        time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
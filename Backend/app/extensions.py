from pymongo import MongoClient
from redis import Redis
from celery import Celery
from slowapi import Limiter
from slowapi.util import get_remote_address


class MongoDBClient:
    def __init__(self):
        self.client = None
        self.db = None

    def init(self, mongodb_uri: str):
        self.client = MongoClient(mongodb_uri)
        db_name = mongodb_uri.split('/')[-1].split('?')[0]
        self.db = self.client[db_name]


class RedisClient:
    def __init__(self):
        self.client = None

    def init(self, redis_url: str):
        self.client = Redis.from_url(redis_url, decode_responses=True)


mongo = MongoDBClient()
redis_client = RedisClient()
celery = Celery('financial_analyzer')
limiter = Limiter(key_func=get_remote_address)

from flask_pymongo import PyMongo
from redis import Redis
from celery import Celery

class MongoDBClient:
    def __init__(self):
        self.client = None
        self.db = None
    
    def init_app(self, app):
        self.client = PyMongo(app)
        self.db = self.client.db

class RedisClient:
    def __init__(self):
        self.client = None
    
    def init_app(self, app):
        redis_url = app.config['REDIS_URL']
        self.client = Redis.from_url(redis_url, decode_responses=True)

mongo = MongoDBClient()
redis_client = RedisClient()
celery = Celery('financial_analyzer')
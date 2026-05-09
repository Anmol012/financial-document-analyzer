from config import Config
from app.extensions import mongo, redis_client, celery

# Init datastores for Celery worker process
mongo.init(Config.MONGODB_URI)
redis_client.init(Config.REDIS_URL)

celery.conf.update(
    broker_url=Config.CELERY_BROKER_URL,
    result_backend=Config.CELERY_RESULT_BACKEND,
)

# Import tasks so Celery can discover them
import app.tasks.analysis_tasks  # noqa: F401

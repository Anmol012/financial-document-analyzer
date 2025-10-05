from app import create_app
from app.extensions import celery
from config import Config

app = create_app(Config)
app.app_context().push()
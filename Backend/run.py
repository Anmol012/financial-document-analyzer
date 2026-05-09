import uvicorn
from app import create_app
from config import Config
import os

os.makedirs('uploads', exist_ok=True)
os.makedirs('logs', exist_ok=True)

app = create_app(Config)

if __name__ == '__main__':
    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=5000,
        reload=Config.APP_ENV == 'development',
    )

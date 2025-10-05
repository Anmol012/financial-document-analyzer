from app import create_app
from config import Config
import os

# Create necessary directories
os.makedirs('uploads', exist_ok=True)
os.makedirs('logs', exist_ok=True)

app = create_app(Config)

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.FLASK_ENV == 'development'
    )
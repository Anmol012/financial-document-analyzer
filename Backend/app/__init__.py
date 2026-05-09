from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from config import Config
from app.extensions import mongo, redis_client, celery, limiter
import logging


def create_app(config_class=Config) -> FastAPI:
    logging.basicConfig(level=getattr(logging, config_class.LOG_LEVEL, logging.INFO))

    app = FastAPI(title="Financial Document Analyzer API", version="1.0.0")

    origins = ['*'] if config_class.CORS_ORIGINS.strip() == '*' else [
        o.strip() for o in config_class.CORS_ORIGINS.split(',')
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Validation errors as 400 (consistent with Flask behaviour)
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request, exc):
        first = exc.errors()[0] if exc.errors() else {}
        msg = first.get('msg', 'Validation error')
        return JSONResponse(status_code=400, content={'error': msg})

    # Init datastores
    mongo.init(config_class.MONGODB_URI)
    redis_client.init(config_class.REDIS_URL)

    # Configure Celery
    celery.conf.update(
        broker_url=config_class.CELERY_BROKER_URL,
        result_backend=config_class.CELERY_RESULT_BACKEND,
    )

    # MongoDB indexes
    try:
        mongo.db.users.create_index('email', unique=True)
        mongo.db.documents.create_index('user_id')
        mongo.db.analyses.create_index('document_id')
        mongo.db.analyses.create_index([('user_id', 1), ('completed_at', -1)])
    except Exception as e:
        logging.warning(f'Could not create indexes: {e}')

    # Routers
    from app.routes.auth import router as auth_router
    from app.routes.documents import router as docs_router
    from app.routes.analysis import router as analysis_router

    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(docs_router, prefix="/api/documents", tags=["documents"])
    app.include_router(analysis_router, prefix="/api/analysis", tags=["analysis"])

    return app

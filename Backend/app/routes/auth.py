from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from jose import JWTError, jwt
from datetime import datetime, timedelta
from bson import ObjectId
import bcrypt
import uuid
import logging

from config import Config
from app.extensions import mongo, redis_client, limiter
from app.dependencies import get_current_user, ALGORITHM

router = APIRouter()
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ─── Pydantic schemas ────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ─── Token helpers ───────────────────────────────────────────────────────────

def _make_token(user_id: str, role: str, expires: timedelta, token_type: str) -> tuple[str, str, int]:
    jti = str(uuid.uuid4())
    exp = datetime.utcnow() + expires
    payload = {
        "sub": user_id,
        "role": role,
        "jti": jti,
        "type": token_type,
        "exp": exp,
    }
    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=ALGORITHM)
    return token, jti, int(exp.timestamp())


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/register", status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, data: RegisterRequest):
    username = data.username.strip()
    email = data.email.strip().lower()
    password = data.password

    if len(username) < 3 or len(username) > 50:
        raise HTTPException(status_code=400, detail="Username must be 3-50 characters")
    if '@' not in email or '.' not in email.split('@')[-1]:
        raise HTTPException(status_code=400, detail="Invalid email address")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    if mongo.db.users.find_one({'email': email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    user_doc = {
        'username': username,
        'email': email,
        'password': hashed,
        'role': 'Viewer',
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
    }
    result = mongo.db.users.insert_one(user_doc)
    logger.info(f"New user registered: {email}")

    return {
        'message': 'User registered successfully',
        'user': {
            'id': str(result.inserted_id),
            'username': username,
            'email': email,
            'role': 'Viewer',
        },
    }


@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest):
    email = data.email.strip().lower()

    user = mongo.db.users.find_one({'email': email})
    if not user or not bcrypt.checkpw(data.password.encode(), user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token, _, _ = _make_token(
        str(user['_id']), user['role'], Config.JWT_ACCESS_TOKEN_EXPIRES, "access"
    )
    refresh_token, _, _ = _make_token(
        str(user['_id']), user['role'], Config.JWT_REFRESH_TOKEN_EXPIRES, "refresh"
    )

    logger.info(f"User logged in: {email}")
    return {
        'message': 'Login successful',
        'token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': str(user['_id']),
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
        },
    }


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    jti = current_user.get('jti')
    exp = current_user.get('exp', 0)
    ttl = int(exp - datetime.utcnow().timestamp())
    if jti and ttl > 0:
        try:
            redis_client.client.setex(f'blocklist:{jti}', ttl, 'revoked')
        except Exception:
            pass
    return {'message': 'Logout successful'}


@router.post("/refresh")
async def refresh(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        access_token, _, _ = _make_token(
            user_id, user['role'], Config.JWT_ACCESS_TOKEN_EXPIRES, "access"
        )
        return {'token': access_token}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


@router.get("/me")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    user = mongo.db.users.find_one({'_id': ObjectId(current_user['sub'])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        'user': {
            'id': str(user['_id']),
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
        }
    }

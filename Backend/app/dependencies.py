from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from config import Config
from app.extensions import redis_client

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        jti = payload.get("jti")
        if jti:
            try:
                if redis_client.client and redis_client.client.get(f'blocklist:{jti}'):
                    raise HTTPException(status_code=401, detail="Token has been revoked. Please log in again.")
            except HTTPException:
                raise
            except Exception:
                pass
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

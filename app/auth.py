from datetime import datetime, timedelta, UTC
from jose import jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    exp = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.jwt_secret, algorithm="HS256")


def create_refresh_token(user_id: int) -> tuple[str, datetime]:
    exp = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    token = jwt.encode(
        {"sub": str(user_id), "exp": exp}, settings.jwt_refresh_secret, algorithm="HS256"
    )
    return token, exp


def decode_access_token(token: str) -> int:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    return int(payload["sub"])


def decode_refresh_token(token: str) -> int:
    payload = jwt.decode(token, settings.jwt_refresh_secret, algorithms=["HS256"])
    return int(payload["sub"])

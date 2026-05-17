from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import JWTError
from app.database import get_db
from app import models, schemas
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)

router = APIRouter()


@router.post("/register", response_model=schemas.TokenResponse, status_code=201)
def register(body: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = models.User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_tokens(user, db)


@router.post("/login", response_model=schemas.TokenResponse)
def login(body: schemas.UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _issue_tokens(user, db)


@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh(body: schemas.RefreshRequest, db: Session = Depends(get_db)):
    try:
        user_id = decode_refresh_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    stored = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token == body.refresh_token)
        .first()
    )
    if not stored or stored.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(status_code=401, detail="Refresh token expired or revoked")

    db.delete(stored)
    db.commit()

    user = db.get(models.User, user_id)
    return _issue_tokens(user, db)


def _issue_tokens(user: models.User, db: Session) -> schemas.TokenResponse:
    access = create_access_token(user.id)
    refresh, exp = create_refresh_token(user.id)
    db.add(models.RefreshToken(token=refresh, user_id=user.id, expires_at=exp))
    db.commit()
    return schemas.TokenResponse(access_token=access, refresh_token=refresh)

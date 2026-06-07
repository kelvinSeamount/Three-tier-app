from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import models, schemas
from .database import get_db
import os

# SECRET_KEY is like the recipe for your lock combination.
# In production, this comes from a Kubernetes Secret (never hardcode it).
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-use-k8s-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# CryptContext handles password hashing.
# bcrypt is the "food safe container" — it encrypts passwords so even
# if your database is stolen, raw passwords are not exposed.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# This tells FastAPI: "look for a token in the Authorization header"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    """
    Creates a JWT token — think of it like a numbered wristband at a festival.
    You get it at the entrance (login), and show it at every beer stand (API call)
    to prove you already paid. It expires after 30 minutes.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    FastAPI calls this on every protected route.
    It decodes the JWT wristband and returns the user it belongs to.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

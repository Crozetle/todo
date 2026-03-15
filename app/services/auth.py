from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.users import create_user, get_user_by_username

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def register_user(db: Session, username: str, password: str) -> User:
    existing = get_user_by_username(db, username)
    if existing:
        raise ValueError(f"Username '{username}' is already taken")
    hashed = hash_password(password)
    return create_user(db, username, hashed)

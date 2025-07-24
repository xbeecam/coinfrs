from sqlmodel import Session, select
from typing import Optional
from app.models.canonical import User
from app.schemas.user import UserCreate
from app.core.security import hash_password

def get_user_by_email(session: Session, *, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def get_user_by_google_id(session: Session, *, google_id: str) -> User | None:
    statement = select(User).where(User.google_auth_id == google_id)
    return session.exec(statement).first()

def create_user(session: Session, *, user_in: UserCreate) -> User:
    hashed_password = hash_password(user_in.password) if user_in.password else None
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        is_active=True,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def create_oauth_user(
    session: Session, 
    *, 
    email: str, 
    google_auth_id: str
) -> User:
    db_user = User(
        email=email,
        google_auth_id=google_auth_id,
        is_active=True,
        hashed_password=None  # OAuth users don't have passwords
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

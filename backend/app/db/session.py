from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.pool import NullPool, QueuePool
from typing import Generator
import os
from contextlib import contextmanager


# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/coinfrs")

# Create engine with appropriate pooling
if "test" in DATABASE_URL:
    # Use NullPool for testing to avoid connection issues
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, poolclass=NullPool)
else:
    # Use QueuePool for production/development
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,  # Recycle connections after 1 hour
    )


def init_db():
    """Initialize database - create all tables."""
    # Import all models to ensure they're registered
    from app.models import canonical, onboarding, staging
    from app.db.base import BaseModel
    
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Usage in FastAPI:
        @app.get("/items/")
        def read_items(session: Session = Depends(get_session)):
            ...
    """
    with Session(engine) as session:
        yield session


@contextmanager
def get_db_session():
    """
    Context manager for database session.
    Usage:
        with get_db_session() as session:
            user = session.get(User, user_id)
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class DatabaseSessionManager:
    """
    Database session manager for use in services.
    Provides both context manager and dependency injection patterns.
    """
    
    def __init__(self):
        self.engine = engine
    
    @contextmanager
    def session(self):
        """Get a database session as context manager."""
        with Session(self.engine) as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
    
    def get_session(self) -> Session:
        """Get a new session (caller responsible for closing)."""
        return Session(self.engine)


# Global session manager instance
db_manager = DatabaseSessionManager()
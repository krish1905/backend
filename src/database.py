"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Determine if using SQLite (exported for use in models.py)
is_sqlite = settings.database_url.startswith("sqlite")

__all__ = ['Base', 'SessionLocal', 'engine', 'get_db', 'is_sqlite']

# Create engine with appropriate settings
if is_sqlite:
    # SQLite-specific settings
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        echo=settings.debug
    )
else:
    # PostgreSQL settings
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=settings.debug
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


# Dependency to get database session
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


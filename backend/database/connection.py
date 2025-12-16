"""Database connection and session management."""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://odyssai:odyssai_password@localhost:5432/odyssai_db"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    try:
        from database.models import User, UserProfile, Trip
        Base.metadata.create_all(bind=engine)
        print("Database tables initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise


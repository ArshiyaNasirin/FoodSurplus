"""
database.py - SQLite database setup using SQLAlchemy.
Provides thread-safe sessions, table initialization, and SQLite foreign key enforcement.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

SYNC_DATABASE_URL = "sqlite:///./foodresq.db"

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

@event.listens_for(sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enforce foreign key constraints for SQLite connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

SessionLocal = SyncSessionLocal

def get_db():
    """FastAPI dependency that yields a thread-safe SQLAlchemy DB session."""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_sync_db():
    """Synchronous session generator."""
    return get_db()

def init_db():
    """Create all tables synchronously in the database."""
    Base.metadata.create_all(bind=sync_engine)

def init_sync_db():
    """Create all tables synchronously in the database."""
    init_db()

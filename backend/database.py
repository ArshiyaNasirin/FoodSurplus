"""
database.py - SQLite database setup using SQLAlchemy.
Provides thread-safe sessions, table initialization, and SQLite foreign key enforcement.
"""

import os
import shutil
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        tmp_db = "/tmp/foodresq.db"
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        orig_db = os.path.join(base_dir, "foodresq.db")
        if not os.path.exists(tmp_db) and os.path.exists(orig_db):
            try:
                shutil.copy2(orig_db, tmp_db)
            except Exception as e:
                pass
        SYNC_DATABASE_URL = f"sqlite:///{tmp_db}"
    else:
        SYNC_DATABASE_URL = "sqlite:///./foodresq.db"
else:
    SYNC_DATABASE_URL = DATABASE_URL

class Base(DeclarativeBase):
    pass

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if SYNC_DATABASE_URL.startswith("sqlite") else {}
)

@event.listens_for(sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if SYNC_DATABASE_URL.startswith("sqlite"):
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
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_sync_db():
    return get_db()

def init_db():
    try:
        Base.metadata.create_all(bind=sync_engine)
    except Exception as e:
        print("[WARN] init_db warning:", e)

def init_sync_db():
    init_db()

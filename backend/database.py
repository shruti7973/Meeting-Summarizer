# File: backend/database.py

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DB_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(
    DB_DIR,
    "meeting_summarizer.db",
)

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    future=True,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db():
    """
    Provide a SQLAlchemy database session to FastAPI
    and close it after the request is completed.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()  
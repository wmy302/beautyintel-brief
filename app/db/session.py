from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings, root_path


def _database_url() -> str:
    url = get_settings().database_url
    if url.startswith("sqlite:///./"):
        root_path("data").mkdir(exist_ok=True)
    return url


engine = create_engine(_database_url(), connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


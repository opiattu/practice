import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не задан")

if DATABASE_URL.startswith("https://eckxvbayzgasuugeuphe.supabase.co"):
    DATABASE_URL = DATABASE_URL.replace("https://eckxvbayzgasuugeuphe.supabase.co", "https://eckxvbayzgasuugeuphe.supabase.co", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
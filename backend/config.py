import os
from dotenv import load_dotenv
from pathlib import Path

# Находим корневую папку проекта (где лежит .env)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/practice")
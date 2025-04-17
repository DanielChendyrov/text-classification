# db/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Always use DATABASE_URL from environment (should point to PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"[DB] Using DATABASE_URL: {DATABASE_URL}")
if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable is required and must point to the shared PostgreSQL instance.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

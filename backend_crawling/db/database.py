from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/newspaper_crawler")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Define CrawledData model
class CrawledData(Base):
    __tablename__ = "crawled_data"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    contents = Column(String, nullable=True)
    analysis = Column(String, nullable=True)
    crawled_at = Column(DateTime, default=datetime.utcnow)
    is_analyzed = Column(Boolean, default=False)
    analyzed_at = Column(DateTime, nullable=True)
    analyze_success = Column(Boolean, default=None)  # None=not analyzed, True=success, False=failure

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)
# db/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()

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

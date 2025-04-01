# db/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CrawledData(Base):
    __tablename__ = "crawled_data"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False, index=True)
    contents = Column(String, nullable=False, index=True)
    analysis = Column(String, nullable=True, index=True)
    crawled_at = Column(DateTime, nullable=False, default=func.now())
    is_analyzed = Column(Boolean, nullable=False, default=False, index=True)
    analyzed_at = Column(DateTime, nullable=True)

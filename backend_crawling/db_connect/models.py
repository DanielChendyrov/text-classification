from psycopg2 import connect
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database import Base

class CrawledData(Base):
    __tablename__ = "crawled_data"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    url = Column(String, nullable=False, index=True)
    contents = Column(String, nullable=False, index=True)
    analysis = Column(String, nullable=True, index=True)
    crawled_at = Column(DateTime, nullable=False)
    is_analyzed = Column(Boolean, nullable=False, index=True)
    analyzed_at = Column(DateTime, nullable=True)

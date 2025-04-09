# db/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Nếu dùng sqlite, thêm connect_args
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def seed_db():
    """Hàm này thêm dữ liệu giả để test nếu bảng crawled_data còn trống."""
    from db.models import CrawledData
    session = SessionLocal()
    # Nếu chưa có dữ liệu, thêm vài record giả
    if not session.query(CrawledData).first():
        fake_articles = [
            CrawledData(
                url="https://vtcnews.vn/my-ap-thue-46-hang-nhap-tu-viet-nam-thi-truong-bat-dong-san-co-bi-anh-huong-ar935593.html",
                contents="""""",
                analysis=None,
                is_analyzed=False
            ),
            CrawledData(
                url="https://vtv.vn/doi-song/lam-dich-vu-visa-khong-co-nghia-la-bao-dau-100-20250114201050295.htm",
                contents="""""",
                analysis=None,
                is_analyzed=False
            ),
        ]
        session.add_all(fake_articles)
        session.commit()
    session.close()

# routers/analysis.py
import os
import httpx
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db.models import CrawledData
from db.database import SessionLocal

router = APIRouter()

# Dependency để lấy DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Lấy API key từ biến môi trường
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API")
if not DEEPSEEK_API_KEY:
    raise Exception("Thiếu biến môi trường DEEPSEEK_API")

@router.post("/analyze")
def analyze_articles(db: Session = Depends(get_db)):
    """
    Phân tích các bài báo chưa được phân tích (is_analyzed == False)
    bằng cách gọi Deepseek API.
    """
    articles = db.query(CrawledData).filter(CrawledData.is_analyzed == False).all()
    if not articles:
        return {"detail": "Không có bài báo nào cần phân tích"}

    for article in articles:
        try:
            response = httpx.post(
                "https://api.deepseek.com/analyze",  # Thay đổi URL theo tài liệu của Deepseek
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                json={"content": article.contents},
                timeout=30.0
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            print(f"Lỗi khi gọi Deepseek API cho bài báo {article.id}: {e}")
            continue

        result = response.json()
        # Giả sử kết quả phân tích nằm trong key "report"
        article.analysis = result.get("report", "")
        article.is_analyzed = True
        article.analyzed_at = datetime.utcnow()
        db.add(article)

    db.commit()
    return {"detail": "Phân tích bài báo thành công"}

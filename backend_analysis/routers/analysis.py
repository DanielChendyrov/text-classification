import os
import httpx
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db.models import CrawledData
from db.database import SessionLocal

router = APIRouter()


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
    Sử dụng DeepSeek Chat Completions API để phân tích các bài báo chưa được phân tích.
    Mỗi bài báo sẽ được gửi dưới dạng message để model deepseek-chat phân tích và trả về báo cáo.
    """
    articles = db.query(CrawledData).filter(CrawledData.is_analyzed == False).all()
    if not articles:
        return {"detail": "Không có bài báo nào cần phân tích"}

    for article in articles:
        # Xây dựng payload theo định dạng của DeepSeek Chat API
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "Bạn là một chuyên gia phân tích bài báo. Vui lòng phân tích bài viết sau và cung cấp một báo cáo chi tiết về nội dung, chủ đề và giọng điệu, cảm xúc của bài báo."
                },
                {
                    "role": "user",
                    "content": article.contents
                }
            ],
            "max_tokens": 2048,
            "temperature": 1,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stream": False,
            "response_format": {"type": "text"}
        }

        try:
            response = httpx.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
                },
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            print(f"Lỗi khi gọi DeepSeek API cho bài báo {article.id}: {e}")
            continue

        data = response.json()
        try:
            # Trích xuất nội dung báo cáo từ kết quả trả về
            analysis_report = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            print(f"Lỗi khi trích xuất báo cáo cho bài báo {article.id}: {e}")
            analysis_report = ""

        article.analysis = analysis_report
        article.is_analyzed = True
        article.analyzed_at = datetime.utcnow()
        db.add(article)

    db.commit()
    return {"detail": "Phân tích bài báo thành công"}

import os
import json
import logging
import asyncio
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import CrawledData
from db.database import SessionLocal

# Import Newspaper3k để lấy nội dung bài báo
from newspaper import Article

router = APIRouter()

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Lấy API key DeepSeek từ biến môi trường (đã load từ file .env trong main.py)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API")
if not DEEPSEEK_API_KEY:
    raise Exception("Thiếu biến môi trường DEEPSEEK_API")

def download_and_parse(url: str) -> str:
    """
    Sử dụng Newspaper3k để tải và phân tích bài báo từ URL.
    Chúng ta thiết lập ngôn ngữ là tiếng Việt để phù hợp với bài báo.
    """
    try:
        article = Article(url, language='vi')
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        logger.error(f"[Newspaper3k] Lỗi khi xử lý {url}: {e}")
        return ""

async def fetch_content(url: str) -> str:
    """
    Chạy hàm download_and_parse trong executor để không block event loop.
    Log preview (500 ký tự đầu tiên) của nội dung crawl được.
    """
    loop = asyncio.get_event_loop()
    content = await loop.run_in_executor(None, download_and_parse, url)
    logger.info(f"[Newspaper3k] URL: {url}, content preview (500 ký tự): {content[:500]}")
    return content

@router.post("/analyze")
async def analyze_articles(db: Session = Depends(get_db)):
    """
    Đối với mỗi bài báo trong DB (chỉ lưu URL):
      1. Lấy nội dung bài báo bằng Newspaper3k.
      2. Gửi nội dung đến DeepSeek API để phân tích và trả lời bằng tiếng Việt.
      3. Cập nhật báo cáo phân tích vào DB.
    """
    articles = db.query(CrawledData).filter(CrawledData.is_analyzed == False).all()
    if not articles:
        logger.info("Không có bài báo nào cần phân tích")
        return {"detail": "Không có bài báo nào cần phân tích"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        for article in articles:
            logger.info(f"[Analyze] Đang xử lý bài báo có URL: {article.url}")
            content = await fetch_content(article.url)
            if not content:
                logger.error(f"[Analyze] Không lấy được nội dung cho URL: {article.url}")
                continue

            # Xây dựng payload cho DeepSeek API
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",

                        "content": "Bạn là một chuyên gia phân tích tin tức. Nhiệm vụ của bạn là **đọc kỹ bài báo sau và xác định cảm xúc chủ đạo** mà nó truyền tải. Hãy **phân loại cảm xúc này vào một trong các danh mục sau:** [Tích cực, Tiêu cực, Trung lập, Hài hước, Phẫn nộ, Bất ngờ, Buồn bã]. Sau khi phân loại, hãy **đưa ra một nhận xét tổng quan ngắn gọn (tối đa 2 câu)** về nội dung chính của bài báo, **dựa trên cảm xúc bạn đã xác định**."
                    },
                    {
                        "role": "user",
                        "content": content
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

            logger.info(f"[DeepSeek] Payload cho URL {article.url}: {json.dumps(payload, ensure_ascii=False)}")
            try:
                response = await client.post(
                    "https://api.deepseek.com/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
                    },
                    json=payload
                )
                if response.status_code != 200:
                    logger.error(f"[DeepSeek] Error for URL {article.url} - Status Code: {response.status_code}")
                    logger.error(f"[DeepSeek] Response: {response.text}")
                    continue

                data = response.json()
                try:
                    analysis_report = data["choices"][0]["message"]["content"]
                    logger.info(f"[DeepSeek] Nhận báo cáo thành công cho URL {article.url}")
                except (KeyError, IndexError) as e:
                    logger.error(f"[DeepSeek] Lỗi khi trích xuất báo cáo cho URL {article.url}: {e}")
                    logger.error(f"[DeepSeek] Full response: {json.dumps(data, indent=2)}")
                    analysis_report = ""
            except httpx.HTTPError as e:
                logger.exception(f"[DeepSeek] Lỗi khi gọi DeepSeek API cho URL {article.url}: {e}")
                continue

            # Cập nhật thông tin phân tích vào DB
            article.analysis = analysis_report
            article.is_analyzed = True
            article.analyzed_at = datetime.utcnow()
            db.add(article)
    db.commit()
    logger.info("Cập nhật phân tích xong cho tất cả bài báo")
    return {"detail": "Phân tích bài báo thành công"}

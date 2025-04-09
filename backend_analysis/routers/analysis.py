import os
import json
import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import CrawledData
from db.database import SessionLocal

# Import các module của crawl4ai
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

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

async def fetch_content(url: str) -> str:
    """
    Crawl bài báo từ URL sử dụng crawl4ai.
    Trích xuất toàn bộ nội dung chính của bài báo dưới dạng văn bản thuần,
    loại bỏ các phần không liên quan như tiêu đề, menu, quảng cáo, điều hướng, bình luận, chân trang.
    """
    extraction_instruction = (
        "Trích xuất và trả về toàn bộ nội dung chính của bài báo dưới dạng văn bản thuần. "
        "Không cắt bỏ hay rút gọn nội dung; trả về toàn bộ bài báo, bao gồm tất cả các đoạn văn liên tục thể hiện nội dung chính. "
        "Loại bỏ hoàn toàn các phần không liên quan như điều hướng, quảng cáo, bình luận và chân trang."
    )
    schema = {
        "type": "object",
        "properties": {
            "content": {"type": "string"}
        },
        "required": ["content"]
    }
    llm_strategy = LLMExtractionStrategy(
        provider="deepseek/deepseek-chat",
        api_token=DEEPSEEK_API_KEY,
        schema=schema,
        extraction_type="schema",
        instruction=extraction_instruction,
        chunk_token_threshold=1000,
        overlap_rate=0.0,
        apply_chunking=True,
        input_format="markdown",
        extra_args={"temperature": 0.0, "max_tokens": 2048},
    )

    crawl_config = CrawlerRunConfig(
        extraction_strategy=llm_strategy,
        cache_mode=CacheMode.BYPASS,
        process_iframes=False,
        remove_overlay_elements=True,
        exclude_external_links=True,
    )

    browser_cfg = BrowserConfig(headless=True, verbose=False)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=crawl_config)
        if result.success:
            try:
                parsed = json.loads(result.extracted_content)
                if isinstance(parsed, list):
                    content = parsed[0].get("content", "") if parsed and isinstance(parsed[0], dict) else ""
                elif isinstance(parsed, dict):
                    content = parsed.get("content", "")
                else:
                    content = ""
                logger.info(f"[Crawl] URL: {url}, content preview (500 ký tự): {content[:500]}")
                return content
            except Exception as e:
                logger.error(f"[Crawl] Lỗi khi parse kết quả crawl cho {url}: {e}")
                logger.info(f"[Crawl] Kết quả crawl raw: {result.extracted_content}")
                return ""
        else:
            logger.error(f"[Crawl] Crawl thất bại cho {url}: {result.error_message}")
            return ""

@router.post("/analyze")
async def analyze_articles(db: Session = Depends(get_db)):
    """
    Với mỗi bài báo trong DB (chỉ lưu URL):
      1. Lấy nội dung bài báo bằng Newspaper3k (hoặc crawl4ai) – ở đây sử dụng fetch_content.
      2. Gửi nội dung đến DeepSeek API để phân tích và trả về kết quả bằng tiếng Việt.
      3. Cập nhật báo cáo phân tích vào DB.
    """
    articles = db.query(CrawledData).filter(CrawledData.is_analyzed == False).all()
    if not articles:
        logger.info("Không có bài báo nào cần phân tích")
        return {"detail": "Không có bài báo nào cần phân tích"}

    # Tăng thời gian timeout lên 60 giây
    timeout = httpx.Timeout(60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for article in articles:
            logger.info(f"[Analyze] Đang xử lý bài báo có URL: {article.url}")
            content = await fetch_content(article.url)
            if not content:
                logger.error(f"[Analyze] Không lấy được nội dung cho URL: {article.url}")
                continue

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
            except httpx.ReadTimeout as e:
                logger.error(f"[DeepSeek] ReadTimeout cho URL {article.url}: {e}")
                continue
            except httpx.HTTPError as e:
                logger.exception(f"[DeepSeek] Lỗi khi gọi DeepSeek API cho URL {article.url}: {e}")
                continue

            article.analysis = analysis_report
            article.is_analyzed = True
            article.analyzed_at = datetime.utcnow()
            db.add(article)

    db.commit()
    logger.info("Cập nhật phân tích xong cho tất cả bài báo")
    return {"detail": "Phân tích bài báo thành công"}

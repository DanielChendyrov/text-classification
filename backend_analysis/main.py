import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from dotenv import load_dotenv
load_dotenv()  # Load biến môi trường từ file .env

from fastapi import FastAPI
from routers import analysis
from db.database import init_db, SessionLocal
from sqlalchemy.orm import Session
import logging

app = FastAPI(title="Backend Analysis API", debug=True)

# Hàm tự động phân tích các bài báo chưa crawl
async def auto_analyze_articles():
    db = SessionLocal()
    try:
        articles = db.query(CrawledData).filter(CrawledData.is_analyzed == False).all()
        if articles:
            logging.info(f"Đang phân tích {len(articles)} bài báo chưa phân tích.")
            # Gọi hàm analyze_articles để phân tích
            await analysis.analyze_articles(db)
        else:
            logging.info("Không có bài báo nào cần phân tích.")
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra và phân tích bài báo: {e}")
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    # Khởi tạo database (và seed dữ liệu nếu cần)
    init_db()
    # Kiểm tra và tự động phân tích các bài báo chưa phân tích
    await auto_analyze_articles()

# Include router cho endpoint phân tích
app.include_router(analysis.router, prefix="/api", tags=["analysis"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)

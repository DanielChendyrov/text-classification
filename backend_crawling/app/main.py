import os
import logging
import time
from datetime import datetime
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler

from app.db.database import init_db, SessionLocal
from app.routers import crawler
from app.utils.crawler import load_config, crawl_website
from app.db.database import CrawledData

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("app")

# Initialize FastAPI app
app = FastAPI(title="Newspaper URL Crawler")

# Include routers
app.include_router(crawler.router, prefix="/api", tags=["crawler"])

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Scheduled task to crawl websites
def scheduled_crawling():
    """
    Function to crawl websites on a schedule.
    Creates a new database session for each scheduled run.
    """
    logger.info(f"Starting scheduled crawling at {datetime.utcnow()}")
    db = SessionLocal()
    try:
        config = load_config()
        
        for website in config["websites"]:
            if website.get("active", True):
                base_url = website["base_url"]
                logger.info(f"Scheduled crawl for {website['name']} ({base_url})")
                
                article_urls = crawl_website(base_url)
                
                saved_count = 0
                for url in article_urls:
                    # Check if URL already exists in the database
                    existing = db.query(CrawledData).filter(CrawledData.url == url).first()
                    if not existing:
                        # Create new entry
                        new_entry = CrawledData(
                            url=url,
                            crawled_at=datetime.utcnow(),
                            is_analyzed=False
                        )
                        db.add(new_entry)
                        saved_count += 1
                
                # Commit after each website to avoid losing all data if one fails
                db.commit()
                logger.info(f"Saved {saved_count} new articles from {website['name']}")
                
        logger.info(f"Completed scheduled crawling at {datetime.utcnow()}")
    except Exception as e:
        logger.error(f"Error during scheduled crawling: {e}")
        db.rollback()
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    """
    Initialize database and start scheduler on application startup
    """
    logger.info("Initializing application...")
    
    # Create database tables if they don't exist
    init_db()
    logger.info("Database tables created")
    
    # Set up scheduler
    config = load_config()
    crawl_interval = config.get("crawl_interval_minutes", 30)
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_crawling, 'interval', minutes=crawl_interval)
    scheduler.start()
    logger.info(f"Scheduler started with interval of {crawl_interval} minutes")
    
    # Run initial crawl
    logger.info("Starting initial crawl...")
    scheduled_crawling()

@app.get("/")
async def root():
    return {"message": "Newspaper URL Crawler API is running"}

# If running directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
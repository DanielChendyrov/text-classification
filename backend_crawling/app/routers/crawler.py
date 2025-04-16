import logging
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import SessionLocal, CrawledData
from app.utils.crawler import load_config, crawl_website

router = APIRouter()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("crawler_router")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/crawl")
async def start_crawling(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Start the crawling process in the background.
    Returns immediately while crawling runs in the background.
    """
    background_tasks.add_task(crawl_all_websites, db)
    return {"detail": "Crawling started in the background"}

@router.get("/status")
async def get_status(db: Session = Depends(get_db)):
    """
    Get the current status of crawled articles
    """
    total_count = db.query(CrawledData).count()
    today_count = db.query(CrawledData).filter(
        CrawledData.crawled_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    return {
        "total_articles_crawled": total_count,
        "articles_crawled_today": today_count,
        "last_check": datetime.utcnow()
    }

def crawl_all_websites(db: Session):
    """
    Crawl all websites in the config file and store the URLs in the database.
    """
    try:
        config = load_config()
        
        for website in config["websites"]:
            if website.get("active", True):
                base_url = website["base_url"]
                logger.info(f"Starting crawl for {website['name']} ({base_url})")
                
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
                
        logger.info("Completed crawling all websites")
    except Exception as e:
        logger.error(f"Error during crawling: {e}")
        # Make sure to roll back on error
        db.rollback()
        raise
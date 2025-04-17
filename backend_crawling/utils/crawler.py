import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import List, Dict, Any
from db.database import SessionLocal  # Adjusted import path to match relative structure

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("crawler")

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "websites.json"))

def load_config() -> Dict[str, Any]:
    """Load the configuration from the JSON file"""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[Config] Error loading config: {e}")
        return {"websites": [], "crawl_interval_minutes": 30}

def is_article_url(url: str) -> bool:
    """Check if the URL is likely an article URL based on patterns"""
    # Common article URL patterns in Vietnamese news sites
    article_patterns = [
        r"/\d{4}/\d{2}/",  # Date patterns like /2023/04/
        r"/tin-tuc/",
        r"/bai-viet/",
        r"/suc-khoe/",
        r"/the-gioi/",
        r"/kinh-doanh/",
        r"/giai-tri/",
        r"/the-thao/",
        r"/phap-luat/",
        r"/giao-duc/",
        r"/du-lich/"
    ]
    
    for pattern in article_patterns:
        if re.search(pattern, url):
            return True
    
    # Ignore common non-article URLs
    ignore_patterns = [
        r"/tag/",
        r"/tags/",
        r"/search/",
        r"/login/",
        r"/register/",
        r"/rss/",
        r"/feed/",
        r"\.(jpg|jpeg|png|gif|pdf|mp3|mp4)$"
    ]
    
    for pattern in ignore_patterns:
        if re.search(pattern, url):
            return False
    
    return True  # Default to True for URLs that don't match any pattern

def crawl_website(base_url: str) -> List[str]:
    """Crawl a website for article URLs"""
    article_urls = set()
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all links in the page
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(base_url, href)
            
            # Skip URLs from other domains
            if urlparse(full_url).netloc != urlparse(base_url).netloc:
                continue
                
            # Check if it's an article URL
            if is_article_url(full_url):
                article_urls.add(full_url)
        
        logger.info(f"Found {len(article_urls)} article URLs from {base_url}")
        return list(article_urls)
        
    except Exception as e:
        logger.error(f"Error crawling {base_url}: {e}")
        return []

def scheduled_crawling():
    logger.info(f"Starting scheduled crawling at {datetime.now(timezone.utc)}")
    db = SessionLocal()
    try:
        config = load_config()
        # ...existing code...
    except Exception as e:
        logger.error(f"Error during scheduled crawling: {e}")
        db.rollback()
    finally:
        db.close()
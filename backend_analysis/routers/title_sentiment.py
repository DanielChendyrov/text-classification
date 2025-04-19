# routers/title_sentiment.py
import json
import asyncio
from datetime import datetime, timezone
import os

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models import CrawledData
from transformers import pipeline
from newspaper import Article

router = APIRouter()
os.environ["HUGGINGFACE_HUB_TOKEN"] = os.getenv("HUGGINGFACE_HUB_TOKEN")
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="phong02468/phobert-Vietnamese-newspaper-sentiment",
    tokenizer="phong02468/phobert-Vietnamese-newspaper-sentiment",
    device=-1
)

async def analyze_titles_events():
    db: Session = SessionLocal()
    try:
        articles = db.query(CrawledData).filter(
            CrawledData.title_sentiment == None
        ).all()
        for art in articles:
            # Crawl title
            try:
                article = Article(art.url, language='vi')
                article.download(); article.parse()
                title = article.title or ""
            except:
                title = ""
            # Sentiment
            sentiment = ""
            if title:
                try:
                    res = sentiment_pipeline(title[:512])[0]
                    sentiment = res["label"]
                except:
                    sentiment = ""
            # Update DB
            now = datetime.now(timezone.utc)
            db.query(CrawledData).filter(CrawledData.id==art.id).update({
                CrawledData.title: title,
                CrawledData.title_sentiment: sentiment,
                CrawledData.analyzed_at: now
            })
            db.commit()
            # Emit SSE
            yield f"data: {json.dumps({'url': art.url, 'title': title, 'sentiment': sentiment}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)
    finally:
        db.close()

@router.get("/analyze/stream")
def stream_title_analysis():
    return StreamingResponse(
        analyze_titles_events(),
        media_type="text/event-stream"
    )

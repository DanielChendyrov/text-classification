from dotenv import load_dotenv
import os
# Load .env from the backend_analysis directory explicitly, before any other imports
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

import sys
import asyncio
import logging
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from routers import analysis
from db.database import init_db, SessionLocal
from services.reporting import send_report_email, load_report_config
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("backend_analysis")

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load config from shared config file
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "websites.json"))
def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[Config] Error loading config: {e}")
        return {"websites": [], "analyze_interval_minutes": 30}

app = FastAPI(title="Backend Analysis API", debug=True)

@app.on_event("startup")
async def startup_event():
    init_db()
    # Send report email on startup for debugging/development
    try:
        send_report_email("day")
        send_report_email("week")
    except Exception as e:
        logger.error(f"[Report] Lỗi khi gửi báo cáo khi khởi động: {e}")
    # Set up scheduler for automatic analysis and reporting
    config = load_config()
    report_config = load_report_config()
    interval = config.get("analyze_interval_minutes", 30)
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_analysis_sync, 'interval', minutes=interval)
    # Schedule daily report
    daily_time = report_config.get("daily_report_time", "08:00")
    hour, minute = map(int, daily_time.split(":"))
    scheduler.add_job(lambda: send_report_email("day"), 'cron', hour=hour, minute=minute)
    # Schedule weekly report
    weekly_time = report_config.get("weekly_report_time", "Monday 08:00")
    try:
        weekday, w_time = weekly_time.split()
        w_hour, w_minute = map(int, w_time.split(":"))
        scheduler.add_job(lambda: send_report_email("week"), 'cron', day_of_week=weekday.lower(), hour=w_hour, minute=w_minute)
    except Exception as e:
        logger.error(f"[Report] Lỗi cấu hình thời gian báo cáo tuần: {e}")
    scheduler.start()
    logger.info(f"Analysis scheduler started with interval of {interval} minutes")
    # Run initial analysis
    while True:
        try:
            await run_analysis_async()
            break
        except Exception as e:
            logger.error(f"[DB] Error during initial analysis: {e}. Retrying in 10 seconds...")
            await asyncio.sleep(10)

# Include router for API endpoint (still available for manual trigger)
app.include_router(analysis.router, prefix="/api", tags=["analysis"])

# Refactor: import and expose the analysis logic for scheduler
from routers.analysis import analyze_articles

def run_analysis_sync():
    """Run the analysis in a synchronous context for the scheduler."""
    logger.info("[Scheduler] Running automatic article analysis...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(analyze_articles())

async def run_analysis_async():
    """Run the analysis asynchronously."""
    await analyze_articles()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)

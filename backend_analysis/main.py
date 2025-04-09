
import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from dotenv import load_dotenv
load_dotenv()  # Load biến môi trường từ file .env

from fastapi import FastAPI
from routers import analysis
from db.database import init_db

app = FastAPI(title="Backend Analysis API", debug=True)

@app.on_event("startup")
async def startup_event():
    # Khởi tạo database (và seed dữ liệu nếu cần)
    init_db()


# Include router cho endpoint phân tích
app.include_router(analysis.router, prefix="/api", tags=["analysis"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

from dotenv import load_dotenv
load_dotenv()  # Load các biến môi trường từ file .env

import os
from fastapi import FastAPI
from db.database import init_db, seed_db
from routers import analysis

app = FastAPI(title="Backend Analysis API")

# Khởi tạo DB và seed dữ liệu giả khi khởi động ứng dụng
@app.on_event("startup")
def startup():
    init_db()
    seed_db()

# Include router cho các endpoint phân tích
app.include_router(analysis.router, prefix="/api", tags=["analysis"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

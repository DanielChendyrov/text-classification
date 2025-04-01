# main.py
import os
from fastapi import FastAPI
from db.database import init_db
from routers import analysis

app = FastAPI(title="Backend Analysis API")

# Khởi tạo DB khi ứng dụng khởi động
@app.on_event("startup")
def startup():
    init_db()

# Include router cho phân tích
app.include_router(analysis.router, prefix="/api", tags=["analysis"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

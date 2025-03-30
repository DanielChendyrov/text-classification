import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Annotated
import db_connect.models
from db_connect.database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()

# để tránh bị lỗi CORS, nhập url gốc của đầu truy cập api vào đây
origins = [

]

# setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


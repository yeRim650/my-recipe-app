# app/main.py

import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import init_db
from app.routers import users, user_ingredients, recipes, rag

app = FastAPI(title="My Recipe RAG API")

# CORS 설정 (env 분기)
env = os.getenv("ENV", "development")
origins = ["http://localhost:3000"] if env == "development" else ["https://www.myapp.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

# prefix 끝의 '/' 제거
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(user_ingredients.router, prefix="/api/user_ingredients", tags=["user_ingredients"])
app.include_router(recipes.router, prefix="/api/recipes", tags=["recipes"])
app.include_router(rag.router, prefix="/api/rag", tags=["rag"])

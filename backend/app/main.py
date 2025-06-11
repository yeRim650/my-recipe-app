import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import init_db
from app.routers import ingredients, users, user_ingredients, recipes, rag

app = FastAPI(title="My Recipe RAG API")

# CORS 설정
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

app.include_router(users.router)
app.include_router(user_ingredients.router)
app.include_router(recipes.router)
app.include_router(rag.router)
app.include_router(ingredients.router)
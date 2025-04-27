from fastapi import FastAPI
from app.db import init_db
from app.routers import users, user_ingredients, recipes, rag

app = FastAPI(title="My Recipe RAG API")

@app.on_event("startup")
def on_startup():
    # DB 테이블 생성
    init_db()

# 라우터 등록
app.include_router(users.router,
                   prefix="/api/users",
                   tags=["users"])
app.include_router(user_ingredients.router,
                   prefix="/api/user_ingredients",
                   tags=["user_ingredients"])
app.include_router(recipes.router,
                   prefix="/api/recipes",
                   tags=["recipes"])
app.include_router(rag.router,
                   prefix="/api/rag",
                   tags=["rag"])

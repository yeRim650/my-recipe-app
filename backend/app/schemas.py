# app/schemas.py
from datetime import datetime
from sqlmodel import SQLModel
from typing import Optional

class UserBase(SQLModel):
    username: str
    email:    str

class UserCreate(UserBase):
    """POST/PUT 요청에 쓰이는 스키마: created_at/updated_at 없음"""
    pass

class UserRead(UserBase):
    """응답에 쓰이는 스키마: id, created_at, updated_at 포함"""
    id:           int
    created_at:   datetime
    updated_at:   datetime

    class Config:
        orm_mode = True

class UserIngredientCreate(SQLModel):
    user_id: int
    name:    str
    quantity: float

class UserIngredientRead(UserIngredientCreate):
    created_at: datetime

    class Config:
        orm_mode = True
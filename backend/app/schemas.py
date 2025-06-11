# app/schemas.py
from datetime import datetime
from sqlmodel import SQLModel
from typing import Optional

# ───────────────────────────────────────────────────────────────────────────────
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
        from_attributes = True  # orm_mode 대신 이 옵션 사용

# ───────────────────────────────────────────────────────────────────────────────
class UserIngredientCreate(SQLModel):
    user_id: int
    name:    str
    quantity: float

class UserIngredientRead(SQLModel):
    user_id:    int
    name:       str
    quantity:   float
    created_at: datetime

    class Config:
        from_attributes = True  # orm_mode 대신 이 옵션 사용

# ───────────────────────────────────────────────────────────────────────────────
class IngredientMasterRead(SQLModel):
    """
    Ingredient.master 를 직렬화할 때 쓰는 DTO
    """
    id:   int
    name: str

    class Config:
        from_attributes = True  # orm_mode 대신 이 옵션 사용

# ───────────────────────────────────────────────────────────────────────────────
class IngredientCreate(SQLModel):
    """
    ingredients 테이블에 INSERT 할 때 쓰는 스키마
    """
    recipe_id: int
    master_id: int
    quantity:  Optional[float] = None
    unit:      Optional[str]   = None

class IngredientRead(SQLModel):
    """
    ingredients 테이블에서 SELECT 결과 반환할 때 쓰는 스키마
    """
    id:         int
    recipe_id:  int
    master_id:  int
    quantity:   Optional[float]
    unit:       Optional[str]
    master:     IngredientMasterRead

    class Config:
        from_attributes = True  # orm_mode 대신 이 옵션 사용

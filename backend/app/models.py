# app/models.py

from typing import Optional, List
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String, JSON, DateTime, Integer, Float, UniqueConstraint, Text
from sqlalchemy.sql import func


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str     = Field(sa_column=Column(String(100), unique=True, nullable=False))
    email:    str     = Field(sa_column=Column(String(150), unique=True, nullable=False))

    created_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )

    # (필요시 UserRecipe, UserIngredient 등과의 관계를 추가)
    # recipes: List["UserRecipe"] = Relationship(back_populates="user")
    # ingredients: List["UserIngredient"] = Relationship(back_populates="user")


class IngredientMaster(SQLModel, table=True):
    __tablename__ = "ingredient_master"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str         = Field(sa_column=Column(String(255), unique=True, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )

    # Ingredient 테이블과의 관계
    recipes: List["Ingredient"]         = Relationship(back_populates="master")
    # UserIngredient 테이블과의 관계
    user_ingredients: List["UserIngredient"] = Relationship(back_populates="master")


class UserIngredient(SQLModel, table=True):
    __tablename__ = "user_ingredients"
    __table_args__ = (UniqueConstraint("user_id", "ingredient_id", name="pk_user_ingredient"),)

    user_id:       int       = Field(foreign_key="users.id", primary_key=True)
    ingredient_id: int       = Field(foreign_key="ingredient_master.id", primary_key=True)
    quantity:      float     = Field(default=0.0, sa_column=Column(Float, nullable=False))
    created_at:    datetime  = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )

    # IngredientMaster 쪽 back_populates와 이름을 맞춰야 합니다
    master: IngredientMaster = Relationship(back_populates="user_ingredients")


class Recipe(SQLModel, table=True):
    __tablename__ = "recipes"
    __table_args__ = (UniqueConstraint("recipe_hash", name="uq_recipe_hash"),)

    id:           Optional[int] = Field(default=None, primary_key=True)
    name:         str           = Field(sa_column=Column(String(255), unique=True, nullable=False))
    category:     Optional[str] = Field(default=None, sa_column=Column(String(100)))
    method: Optional[str] = Field(default=None, sa_column=Column(String(100)))      # RCP_WAY2
    description: str | None = Field(
        default=None,
        sa_column=Column(Text)      # ← VARCHAR → TEXT 로 확장
    )
    calories:     Optional[int]
    protein:      Optional[int]
    carbs:        Optional[int]
    fat:          Optional[int]
    sodium:       Optional[int]
    recipe_hash:  str           = Field(sa_column=Column(String(64), unique=True, nullable=False))

    created_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )

    # (필요시) ingredients, instructions, user_recipes 등과의 Relationship 추가


class Ingredient(SQLModel, table=True):
    __tablename__ = "ingredients"
    __table_args__ = (UniqueConstraint("recipe_id", "master_id", name="uq_ing_per_recipe"),)

    id:         Optional[int] = Field(default=None, primary_key=True)
    recipe_id:  int           = Field(foreign_key="recipes.id", nullable=False)
    master_id:  int           = Field(foreign_key="ingredient_master.id", nullable=False)
    quantity:   Optional[float] = Field(default=None, sa_column=Column(Float))
    unit:       Optional[str]

    # IngredientMaster 쪽 recipes와 매칭되는 이름 back_populates="recipes"
    master: IngredientMaster = Relationship(back_populates="recipes")


class IngredientRecipeMapping(SQLModel, table=True):
    __tablename__ = "ingredient_recipe_mapping"

    ingredient_id: int = Field(foreign_key="ingredient_master.id", primary_key=True)
    recipe_id:     int = Field(foreign_key="recipes.id", primary_key=True)


class Instruction(SQLModel, table=True):
    __tablename__ = "instructions"
    __table_args__ = (UniqueConstraint("recipe_id", "step", name="uq_instruction_step"),)

    id:          Optional[int] = Field(default=None, primary_key=True)
    recipe_id:   int           = Field(foreign_key="recipes.id")
    step:        int           = Field(sa_column=Column(Integer, nullable=False))
    instruction: str           = Field(sa_column=Column(String(500), nullable=False))


class UserRecipe(SQLModel, table=True):
    __tablename__ = "user_recipes"

    user_id:   int = Field(foreign_key="users.id",   primary_key=True)
    recipe_id: int = Field(foreign_key="recipes.id", primary_key=True)


class RecipeEmbedding(SQLModel, table=True):
    __tablename__ = "recipe_embeddings"

    recipe_id: int         = Field(foreign_key="recipes.id", primary_key=True)
    embedding: List[float] = Field(sa_column=Column(JSON, nullable=False))

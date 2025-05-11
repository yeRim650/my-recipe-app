from typing import Optional, List
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Integer, UniqueConstraint, JSON, DateTime, Float
from sqlalchemy.sql import func

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str     = Field(sa_column=Column(String, unique=True, nullable=False))
    email:    str     = Field(sa_column=Column(String, unique=True, nullable=False))

    # DB에서 CURRENT_TIMESTAMP 로 채워줍니다
    created_at: datetime = Field(
        sa_column=Column(
            DateTime,
            server_default=func.now(),
            nullable=False
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime,
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False
        )
    )


class UserIngredient(SQLModel, table=True):
    __tablename__ = "user_ingredients"
    __table_args__ = (UniqueConstraint("user_id", "name", name="pk_user_ingredient"),)

    user_id:    int                = Field(foreign_key="users.id", primary_key=True)
    name:       str                = Field(primary_key=True)
    quantity:   float              = Field(
        default=0.0,
        sa_column=Column(Float, nullable=False)
    )
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime,
            server_default=func.now(),
            nullable=False
        )
    )


class Recipe(SQLModel, table=True):
    __tablename__ = "recipes"
    __table_args__ = (UniqueConstraint("recipe_hash", name="uq_recipe_hash"),)

    id:           Optional[int] = Field(default=None, primary_key=True)
    name:         str           = Field(sa_column=Column(String, unique=True, nullable=False))
    category:     Optional[str] = Field(default=None, sa_column=Column(String(100)))
    description:  Optional[str] = None
    calories:     Optional[int] = None
    protein:      Optional[int] = None
    carbs:        Optional[int] = None
    fat:          Optional[int] = None
    sodium:       Optional[int] = None
    recipe_hash:  str           = Field(sa_column=Column(String(64), unique=True, nullable=False))

    created_at: datetime = Field(
        sa_column=Column(
            DateTime,
            server_default=func.now(),
            nullable=False
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime,
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False
        )
    )


class Ingredient(SQLModel, table=True):
    __tablename__ = "ingredients"
    __table_args__ = (UniqueConstraint("recipe_id", "name", name="uq_ingredient_per_recipe"),)

    id:        Optional[int] = Field(default=None, primary_key=True)
    recipe_id: int           = Field(foreign_key="recipes.id")
    name:      str           = Field(sa_column=Column(String, nullable=False))
    quantity:  Optional[float] = None
    unit:      Optional[str]   = None


class Instruction(SQLModel, table=True):
    __tablename__ = "instructions"
    __table_args__ = (UniqueConstraint("recipe_id", "step", name="uq_instruction_step"),)

    id:          Optional[int] = Field(default=None, primary_key=True)
    recipe_id:   int           = Field(foreign_key="recipes.id")
    step:        int           = Field(sa_column=Column(Integer, nullable=False))
    instruction: str           = Field(sa_column=Column(String, nullable=False))


class UserRecipe(SQLModel, table=True):
    __tablename__ = "user_recipes"
    user_id:   int = Field(foreign_key="users.id",   primary_key=True)
    recipe_id: int = Field(foreign_key="recipes.id", primary_key=True)


class RecipeEmbedding(SQLModel, table=True):
    __tablename__ = "recipe_embeddings"

    recipe_id: int         = Field(foreign_key="recipes.id", primary_key=True)
    embedding: List[float] = Field(sa_column=Column(JSON, nullable=False))

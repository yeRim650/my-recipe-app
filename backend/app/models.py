from typing import Optional, List
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Integer, UniqueConstraint, JSON, DateTime

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str       = Field(sa_column=Column(String, unique=True, nullable=False))
    email:    str       = Field(sa_column=Column(String, unique=True, nullable=False))

    # 기본값만 Field()에 지정
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # default, onupdate, nullable 은 Column 안으로
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime,
            default    = datetime.utcnow,
            onupdate   = datetime.utcnow,
            nullable   = False,
        )
    )


class UserIngredient(SQLModel, table=True):
    __tablename__ = "user_ingredients"
    __table_args__ = (UniqueConstraint("user_id", "name", name="pk_user_ingredient"),)

    user_id:       int       = Field(foreign_key="users.id", primary_key=True)
    name:          str       = Field(primary_key=True)  # nullable=False 는 기본값
    created_at:    datetime  = Field(default_factory=datetime.utcnow)


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
    fat:           Optional[int] = None
    sodium:       Optional[int] = None
    recipe_hash:  str           = Field(sa_column=Column(String(64), unique=True, nullable=False))

    created_at:   datetime      = Field(default_factory=datetime.utcnow)
    updated_at:   datetime      = Field(
        sa_column=Column(
            DateTime,
            default    = datetime.utcnow,
            onupdate   = datetime.utcnow,
            nullable   = False,
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

    # nullable=False 은 Column 안으로
    instruction: str           = Field(
        sa_column=Column(String, nullable=False)
    )


class UserRecipe(SQLModel, table=True):
    __tablename__ = "user_recipes"
    user_id:   int = Field(foreign_key="users.id",   primary_key=True)
    recipe_id: int = Field(foreign_key="recipes.id", primary_key=True)


class RecipeEmbedding(SQLModel, table=True):
    __tablename__ = "recipe_embeddings"

    recipe_id: int            = Field(foreign_key="recipes.id", primary_key=True)
    embedding: List[float]    = Field(sa_column=Column(JSON, nullable=False))

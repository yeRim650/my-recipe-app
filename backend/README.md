# My Recipe RAG API

This repository contains a FastAPI application for a Recipe Retrieval Augmented Generation (RAG) system.

## Requirements
- Python 3.8+
- FastAPI
- Uvicorn
- SQLModel
- python-dotenv
- MySQL (or any supported database)

## Installation
```bash
pip install fastapi uvicorn sqlmodel python-dotenv pymysql
````

## Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=""
ENV="development"
```

## Database Initialization

On startup, the application will create tables automatically via `init_db()`. For schema migrations, see [Alembic](https://alembic.sqlalchemy.org/en/latest/).

## Running the Application

Development mode (with auto-reload):

```bash
uvicorn app.main:app --reload
```

Production mode:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

After starting the server, visit:

* Swagger UI: `http://127.0.0.1:8000/docs`
* ReDoc: `http://127.0.0.1:8000/redoc`

## Available Endpoints

* `/api/users` - CRUD for users
* `/api/user_ingredients` - CRUD for user ingredients
* `/api/recipes` - CRUD for recipes
* `/api/rag` - RAG-related endpoints
* `/api/ingredients` - CRUD for ingredients

## CORS Configuration

Allowed origins depend on the `ENV` variable:


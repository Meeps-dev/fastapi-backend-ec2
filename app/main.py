import os
from datetime import datetime
from typing import List

# pyrefly: ignore [missing-import]
import psycopg
# pyrefly: ignore [missing-import]
from psycopg.rows import dict_row
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

app = FastAPI(
    title="fastapi-backend-ec2",
    description="Week 6 FastAPI backend connected to private RDS PostgreSQL",
    version="1.0.0",
)


class UserCreate(BaseModel):
    name: str


class UserResponse(BaseModel):
    id: int
    name: str
    created_at: datetime


def get_db_connection():
    required_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise RuntimeError(f"Missing database environment variables: {', '.join(missing_vars)}")

    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode=os.getenv("DB_SSLMODE", "require"),
        connect_timeout=5,
        row_factory=dict_row,
    )


@app.get("/")
def root():
    return {
        "message": "FastAPI backend is running behind ALB",
        "project": "fastapi-backend-ec2",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "API is running",
        "environment": os.getenv("APP_ENV", "local"),
    }


@app.get("/db-test")
def db_test():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        current_database() AS database,
                        current_user AS user,
                        NOW() AS connected_at;
                    """
                )
                result = cur.fetchone()

        return {
            "status": "ok",
            "message": "Connected to private RDS successfully",
            "database": result["database"],  # pyrefly: ignore
            "user": result["user"],  # pyrefly: ignore
            "connected_at": result["connected_at"],  # pyrefly: ignore
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {exc.__class__.__name__}",
        )


@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (name)
                    VALUES (%s)
                    RETURNING id, name, created_at;
                    """,
                    (user.name,),
                )
                new_user = cur.fetchone()
                conn.commit()

        return new_user

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {exc.__class__.__name__}",
        )


@app.get("/users", response_model=List[UserResponse])
def get_users():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, created_at
                    FROM users
                    ORDER BY id ASC;
                    """
                )
                users = cur.fetchall()

        return users

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch users: {exc.__class__.__name__}",
        )
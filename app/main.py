from typing import List
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()

app = FastAPI(
    title="fastapi-backend-ec2",
    description="Week 6 FastAPI backend deployed on private EC2 behind ALB",
    version="1.0.0",
)

users = []


class UserCreate(BaseModel):
    name: str


class UserResponse(BaseModel):
    id: int
    name: str


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
    return {
        "status": "pending",
        "message": "Database connection will be added on Day 39",
    }


@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):
    new_user = {
        "id": len(users) + 1,
        "name": user.name,
    }

    users.append(new_user)
    return new_user


@app.get("/users", response_model=List[UserResponse])
def get_users():
    return users
from fastapi import FastAPI
from app.db.session import engine
from app.db import models
from app.api.api import api_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Multi-Tenant AI Support Bot")

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Support Bot API"}

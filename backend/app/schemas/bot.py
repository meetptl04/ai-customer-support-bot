import uuid
from pydantic import BaseModel
from typing import List

class FAQItem(BaseModel):
    question: str
    answer: str

class Bot(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID

    class Config:
        from_attributes = True

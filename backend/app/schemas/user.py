import uuid
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: uuid.UUID
    bot_id: uuid.UUID | None = None

    class Config:
        from_attributes = True

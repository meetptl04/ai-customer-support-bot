import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, UniqueConstraint, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id"), nullable=True)
    bot = relationship("Bot", back_populates="users", foreign_keys=[bot_id])
    __table_args__ = (UniqueConstraint('email', 'bot_id', name='_email_bot_uc'),)

class Bot(Base):
    __tablename__ = "bots"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    faqs = Column(JSON, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    owner = relationship("User", foreign_keys=[owner_id])
    users = relationship("User", back_populates="bot", foreign_keys=[User.bot_id])
    chat_history = relationship("ChatHistory", back_populates="bot")
    summaries = relationship("ChatSummary", back_populates="bot")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, index=True, nullable=False)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    role = Column(String, nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    bot = relationship("Bot", back_populates="chat_history")
    user = relationship("User")

class ChatSummary(Base):
    __tablename__ = "chat_summaries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id"), nullable=False)
    session_id = Column(String, unique=True, index=True, nullable=False)
    summary_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    bot = relationship("Bot", back_populates="summaries")


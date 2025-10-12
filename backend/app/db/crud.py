import datetime
from sqlalchemy.orm import Session
import uuid
from . import models
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from sqlalchemy import func, desc 

def get_user_by_email_and_bot(db: Session, email: str, bot_id: uuid.UUID | None):
    return db.query(models.User).filter(models.User.email == email, models.User.bot_id == bot_id).first()

def create_user(db: Session, user: UserCreate, bot_id: uuid.UUID | None = None):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password, bot_id=bot_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_bot(db: Session, bot_id: uuid.UUID):
    return db.query(models.Bot).filter(models.Bot.id == bot_id).first()

def get_bots_by_owner(db: Session, owner_id: uuid.UUID):
    return db.query(models.Bot).filter(models.Bot.owner_id == owner_id).all()

def create_bot(db: Session, name: str, faqs_data: list, owner_id: uuid.UUID):
    db_bot = models.Bot(name=name, faqs=faqs_data, owner_id=owner_id)
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    return db_bot

def get_chat_history(db: Session, session_id: str, bot_id: uuid.UUID, user_id: uuid.UUID, limit: int = 6):
    return db.query(models.ChatHistory).filter(
        models.ChatHistory.session_id == session_id, 
        models.ChatHistory.bot_id == bot_id, 
        models.ChatHistory.user_id == user_id
        ).order_by(models.ChatHistory.timestamp.desc()).limit(limit).all()[::-1]

def get_full_chat_history_by_session(db: Session, session_id: str, user_id: uuid.UUID):
    return db.query(models.ChatHistory).filter(
        models.ChatHistory.session_id == session_id,
        models.ChatHistory.user_id == user_id
    ).order_by(models.ChatHistory.timestamp.asc()).all() 

def get_user_chat_sessions(db: Session, user_id: uuid.UUID, bot_id: uuid.UUID):
    sessions = db.query(
        models.ChatHistory.session_id,
        func.min(models.ChatHistory.message).label('first_message'),
        func.max(models.ChatHistory.timestamp).label('last_updated')
    ).filter(
        models.ChatHistory.user_id == user_id,
        models.ChatHistory.bot_id == bot_id
    ).group_by(
        models.ChatHistory.session_id
    ).order_by(
        desc('last_updated')
    ).all()
    return sessions

def create_chat_message(db: Session, session_id: str, bot_id: uuid.UUID, user_id: uuid.UUID, role: str, message: str):
    db_message = models.ChatHistory(session_id=session_id, bot_id=bot_id, user_id=user_id, role=role, message=message)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_unsummarized_sessions(db: Session, bot_id: uuid.UUID):
    """
    Finds chat sessions for a bot that are either entirely new or have been updated
    since they were last summarized.
    """
    latest_history = db.query(
        models.ChatHistory.session_id,
        func.max(models.ChatHistory.timestamp).label("last_message_time")
    ).filter(models.ChatHistory.bot_id == bot_id).group_by(models.ChatHistory.session_id).subquery()

    existing_summaries = db.query(
        models.ChatSummary.session_id,
        models.ChatSummary.created_at
    ).filter(models.ChatSummary.bot_id == bot_id).subquery()

    sessions_to_process = db.query(
        latest_history.c.session_id,
        models.User.id.label("user_id") 
    ).join(
        models.ChatHistory, latest_history.c.session_id == models.ChatHistory.session_id
    ).join(
        models.User, models.ChatHistory.user_id == models.User.id
    ).outerjoin(
        existing_summaries, latest_history.c.session_id == existing_summaries.c.session_id
    ).filter(
        (existing_summaries.c.session_id == None) | (latest_history.c.last_message_time > existing_summaries.c.created_at)
    ).distinct().all()
    
    return sessions_to_process

def create_chat_summary(db: Session, bot_id: uuid.UUID, session_id: str, summary_text: str):
    """Creates a new summary or updates an existing one for a given session."""
    db_summary = db.query(models.ChatSummary).filter_by(session_id=session_id).first()
    if db_summary:
        db_summary.summary_text = summary_text
        db_summary.created_at = datetime.datetime.utcnow()
    else:
        db_summary = models.ChatSummary(bot_id=bot_id, session_id=session_id, summary_text=summary_text)
        db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary

def get_all_summaries_for_bot(db: Session, bot_id: uuid.UUID):
    return db.query(models.ChatSummary).filter(models.ChatSummary.bot_id == bot_id).all()

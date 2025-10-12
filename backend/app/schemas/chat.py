from pydantic import BaseModel
from datetime import datetime
from typing import List
from .bot import FAQItem

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    suggested_actions: List[str]

class ChatMessage(BaseModel):
    role: str
    message: str
    timestamp: datetime
    class Config:
        from_attributes = True

class ChatSession(BaseModel):
    session_id: str
    first_message: str
    last_updated: datetime
    class Config:
        from_attributes = True

class UserChatSummary(BaseModel):
    summary: str
    session_id: str

class AnalyticsReport(BaseModel):
    bot_name: str
    total_summaries_analyzed: int
    trending_topics: List[str]
    unanswered_questions: List[str]
    suggested_new_faqs: List[FAQItem]

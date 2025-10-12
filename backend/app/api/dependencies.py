import uuid
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from jose import JWTError
from app.db import crud, session, models
from app.schemas.token import TokenData
from app.core.security import jwt
from app.core.config import settings

def get_current_user(authorization: str = Header(...), db: Session = Depends(session.get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token_str = authorization.split(" ")[1]
        payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        email: str = payload.get("sub")
        bot_id_str: str = payload.get("bot_id") 
        
        if email is None:
            raise credentials_exception
        if bot_id_str:
            bot_id = uuid.UUID(bot_id_str)
            user = crud.get_user_by_email_and_bot(db, email=email, bot_id=bot_id)
        else:
            user = db.query(models.User).filter(models.User.email == email, models.User.bot_id == None).first()

    except (JWTError, IndexError, ValueError): 
        raise credentials_exception
    
    if user is None:
        raise credentials_exception
        
    return user

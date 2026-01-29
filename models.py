# models.py 수정본

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# 1. 자식 테이블(Message)을 먼저 두거나, 관계 설정 시 문자열을 사용합니다.
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, nullable=False)
    birth_date = Column(String)
    mbti = Column(String(4))
    gender = Column(String)
    webtoon_level = Column(Integer, default=1)

    # back_populates를 사용하여 양방향 관계 설정
    rooms = relationship("ChatRoom", back_populates="user")

class Character(Base):
    __tablename__ = "characters"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    webtoon_title = Column(String, nullable=False)
    persona = Column(String)
    profile_img = Column(String)

    rooms = relationship("ChatRoom", back_populates="character")

class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    character_id = Column(Integer, ForeignKey("characters.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="rooms")
    character = relationship("Character", back_populates="rooms")
    messages = relationship("Message", back_populates="room")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"))
    sender = Column(String) 
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("ChatRoom", back_populates="messages")
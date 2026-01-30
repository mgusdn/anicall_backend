from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- 사용자(User) 관련 ---
class UserBase(BaseModel):
    nickname: str
    birth_date: Optional[str] = None
    mbti: Optional[str] = None
    gender: Optional[str] = None
    webtoon_level: int = 1

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

# --- 캐릭터(Character) 관련 ---
class CharacterBase(BaseModel):
    name: str
    webtoon_title: str
    school: str
    age: int
    physical: str
    bloodtype: str
    location: str
    family: str
    likes: str
    dislikes: str
    personality: str
    speech_style: str

class CharacterCreate(CharacterBase):
    pass

class CharacterResponse(CharacterBase):
    id: int
    class Config:
        from_attributes = True

# --- 메시지(Message) 관련 ---
class MessageBase(BaseModel):
    content: str
    sender: str  # "user" 또는 "bot"

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    room_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- 채팅방(ChatRoom) 관련 ---
class ChatRoomCreate(BaseModel):
    user_id: int
    character_id: int

class ChatRoomResponse(BaseModel):
    id: int
    user_id: int
    character_id: int
    created_at: datetime
    # 채팅방 조회 시 메시지 내역도 함께 보고 싶다면 아래 주석을 해제하세요.
    # messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True
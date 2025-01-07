from dataclasses import dataclass
from typing import List, Optional, Dict
from pydantic import BaseModel


@dataclass
class Message:
    message: str
    is_received: bool


class MatchProfile(BaseModel):
    match_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    interests: List[str] = []
    looking_for: Optional[str] = None
    location: Optional[str] = None
    distance: Optional[str] = None
    essentials: List[str] = []
    lifestyle: Dict[str, str] = {}
    last_messages: Optional[List[Message]] = None


class OpeningMessageRequest(BaseModel):
    profile: MatchProfile


class MessageResponse(BaseModel):
    message: str


class ReplyRequest(BaseModel):
    profile: MatchProfile
    last_messages: Optional[List[Message]] = None

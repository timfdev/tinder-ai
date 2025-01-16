from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from pydantic import BaseModel


@dataclass
class Message:
    message: str
    is_received: bool

    def model_dump(self):
        return asdict(self)

    def __str__(self):
        direction = "Received" if self.is_received else "Sent"
        return f"[{direction}] {self.message}"


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

    def __str__(self):
        interests = ", ".join(self.interests) if self.interests else "N/A"
        essentials = ", ".join(self.essentials) if self.essentials else "N/A"
        lines = [
            f"Match ID: {self.match_id}",
            f"Name: {self.name or 'N/A'}",
            f"Age: {self.age or 'N/A'}",
            f"Bio: {self.bio or 'N/A'}",
            f"Interests: {interests}",
            f"Looking For: {self.looking_for or 'N/A'}",
            f"Location: {self.location or 'N/A'}",
            f"Distance: {self.distance or 'N/A'}",
            f"Essentials: {essentials}",
            "Lifestyle: " + (", ".join(
                [
                    f"{k} = {v}" for k, v in self.lifestyle.items()
                ]) if self.lifestyle else "N/A"),
        ]
        if self.last_messages:
            lines.append("Last Messages:")
            for msg in self.last_messages:
                lines.append(f"  {msg}")
        else:
            lines.append("Last Messages: N/A")
        return "\n".join(lines)


class OpeningMessageRequest(BaseModel):
    profile: MatchProfile


class MessageResponse(BaseModel):
    message: str


class ReplyRequest(BaseModel):
    profile: MatchProfile
    last_messages: Optional[List[Message]] = None

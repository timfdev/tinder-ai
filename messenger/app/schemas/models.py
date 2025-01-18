from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional
from pydantic import BaseModel, Field
from shared.models import MatchProfile, Message
from langchain.memory import ConversationBufferMemory


class MeetingReadinessOutput(BaseModel):
    """Simple meeting readiness evaluation."""
    ready_to_meet: bool = Field(
        ...,
        description="True if received messages indicate readiness to meet"
    )
    rationale: str = Field(
        ...,
        description="Brief explanation of the decision"
    )


@dataclass
class ConversationState:
    profile: MatchProfile
    messages: List[Message] = field(default_factory=list)
    last_interaction: datetime = field(default_factory=datetime.now)
    _ready_to_meet: bool = field(default=False)  # Storage field
    readiness_timestamp: Optional[datetime] = field(default=None)
    memory: ConversationBufferMemory = field(
        default_factory=lambda: ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="input",
            output_key="output"
        )
    )

    @property
    def ready_to_meet(self) -> bool:
        return self._ready_to_meet

    @ready_to_meet.setter
    def ready_to_meet(self, value: bool) -> None:
        self._ready_to_meet = value
        if value:
            self.readiness_timestamp = datetime.now().replace(microsecond=0)

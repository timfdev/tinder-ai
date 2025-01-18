from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from .database import Base
from shared.models import Message
from messenger.app.schemas.models import ConversationState
from shared.models import MatchProfile


class Chat(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    profile: Mapped[dict] = mapped_column(JSON)  # Stores MatchProfile
    last_interaction: Mapped[datetime] = mapped_column(DateTime)
    ready_to_meet: Mapped[bool] = mapped_column(Boolean, default=False)
    readiness_timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=True
    )

    messages: Mapped[list["MessageDB"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )

    def to_conversation_state(self) -> 'ConversationState':
        state = ConversationState(
            profile=MatchProfile(**self.profile),
            messages=[m.to_message() for m in self.messages],
            last_interaction=self.last_interaction,
            _ready_to_meet=self.ready_to_meet,
            readiness_timestamp=self.readiness_timestamp
        )
        for msg in state.messages:
            (
                state.memory.chat_memory.add_user_message(msg.message)
                if msg.is_received
                else state.memory.chat_memory.add_ai_message(msg.message)
            )
        return state


class MessageDB(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    message: Mapped[str] = mapped_column(String)
    is_received: Mapped[bool] = mapped_column(Boolean)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now().replace(microsecond=0)
    )

    chat = relationship("Chat", back_populates="messages")

    def to_message(self) -> 'Message':
        from shared.models import Message
        return Message(
            message=self.message,
            is_received=self.is_received
        )

    @classmethod
    def from_message(
        cls, message: 'Message', conversation_id: int
    ) -> 'MessageDB':
        return cls(
            conversation_id=conversation_id,
            message=message.message,
            is_received=message.is_received
        )

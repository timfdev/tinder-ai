from messenger.app.schemas.models import ConversationState
from typing import Union


class MatchReadyException(Exception):
    """
    Raised when trying to continue conversation with a match
    that's already ready to meet.
    """
    def __init__(self, state_or_message: Union[ConversationState, str]):
        if isinstance(state_or_message, ConversationState):
            message = (
                f"\nMatch {state_or_message.profile.name} is ready to meet "
                f"(since {state_or_message.readiness_timestamp})"
            )
        else:
            message = str(state_or_message)
        super().__init__(message)

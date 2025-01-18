from messenger.app.schemas.models import ConversationState


class MatchReadyException(Exception):
    """
    Raised when trying to continue conversation with a match
    that's already ready to meet.
    """
    def __init__(self, state: ConversationState):
        super().__init__(
            f"\nMatch {state.profile.name} is ready to meet "
            f"(since {state.readiness_timestamp})"
        )

from typing import Optional


class MatchReadyException(Exception):
    """
    Raised when trying to continue conversation with a match
    that's already ready to meet.
    """
    def __init__(
        self,
        name: Optional[str] = None,
        readiness_timestamp: Optional[str] = None,
        message: Optional[str] = None
    ):
        if message:
            final_message = message
        elif name and readiness_timestamp:
            final_message = (
                f"\nMatch {name} is ready "
                f"to meet (since {readiness_timestamp})"
            )
        else:
            final_message = "Match is ready to meet."
        super().__init__(final_message)

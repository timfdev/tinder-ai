from typing import List, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel
import requests
from urllib.parse import urljoin
from shared.models import (
    MatchProfile,
    MessageResponse,
    OpeningMessageRequest,
    ReplyRequest,
    Message
)


class BaseMessengerService(ABC):
    @abstractmethod
    def generate_opener(
        self, profile: MatchProfile
    ) -> MessageResponse:
        """Generate an opening message based on profile information."""
        pass

    @abstractmethod
    def generate_reply(
        self,
        profile: MatchProfile,
        last_messages: Optional[List[Message]] = None
    ) -> MessageResponse:
        """Generate a reply based on previous messages."""
        pass


class MessengerService:
    def __init__(self, base_url: str, timeout: int = 10, mock: bool = False):
        self.base_url = base_url
        self.timeout = timeout
        self.mock = mock

    def _make_request(self, endpoint: str, data: BaseModel) -> MessageResponse:
        """Make HTTP request to API endpoint"""
        if self.mock:
            return MessageResponse(message="Hello there!")
        else:
            url = urljoin(self.base_url, endpoint)
            response = requests.post(url, json=data.model_dump(), timeout=self.timeout)
            response.raise_for_status()
            return MessageResponse.model_validate(response.json())

    def generate_opener(
            self, profile: MatchProfile
    ) -> MessageResponse:
        """Generate an opening message based on profile information"""
        request = OpeningMessageRequest(profile=profile)
        return self._make_request("/api/generate/opener", request)

    def generate_reply(
        self, profile: MatchProfile,
        last_messages: Optional[List[Message]] = None
    ) -> MessageResponse:
        """Generate a reply based on previous messages"""
        request = ReplyRequest(
            profile=profile,
            last_messages=last_messages
        )
        return self._make_request("/api/generate/reply", request)


# Usage example:
if __name__ == "__main__":
    # Example usage
    messenger = MessengerService("http://localhost:8000", mock=True)
    profile = MatchProfile(
        match_id="123",
        name="Alice",
        age=25,
        bio="Love hiking and photography",
        interests=["travel", "photography"]
    )

    # Generate opener
    opener_response = messenger.generate_opener(
        profile=profile
    )
    print(f"Opening message: {opener_response.message}")

    # Generate reply
    reply_response = messenger.generate_reply(
        profile=profile,
        last_messages=[
            Message(
                message="Hi there!",
                is_received=True
            ),
            Message(
                message="Hey, I love your travel photos!",
                is_received=False
            )
        ]
    )
    print(f"Reply: {reply_response.message}")

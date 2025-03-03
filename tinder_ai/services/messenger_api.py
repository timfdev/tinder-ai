from typing import List, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel
import requests
from urllib.parse import urljoin
from tinder_ai.shared import (
    MatchProfile,
    MessageResponse,
    OpeningMessageRequest,
    ReplyRequest,
    Message,
    MatchReadyException
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
    """
    A service class to interact with the Messenger API.

    Attributes:
        base_url (str): The base URL of the Messenger API.
        timeout (int): The timeout duration for API requests in seconds.

    Methods:
        __init__(base_url: str, timeout: int = 10):
            Initializes the MessengerService with the given base URL and
            timeout.

        _make_request(endpoint: str, data: BaseModel) -> MessageResponse:
            Makes an HTTP POST request to the specified API endpoint with
            the provided data.

        generate_opener(profile: MatchProfile) -> MessageResponse:
            Generates an opening message based on the
            provided profile information.

        generate_reply(profile: MatchProfile,
            last_messages: Optional[List[Message]] = None) -> MessageResponse:
            Generates a reply based on the provided profile information
            and previous messages.
    """
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout

    def _make_request(
        self, endpoint: str, data: BaseModel
    ) -> MessageResponse:
        """Make HTTP request to API endpoint"""
        url = urljoin(self.base_url, endpoint)
        try:
            response = requests.post(
                url, json=data.model_dump(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return MessageResponse.model_validate(response.json())
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                raise MatchReadyException(e.response.json()['detail'])
            raise

    def generate_opener(
            self, profile: MatchProfile,
    ) -> MessageResponse:
        # return MessageResponse(message="Hello, I am a bot")
        """Generate an opening message based on profile information"""
        request = OpeningMessageRequest(profile=profile)
        return self._make_request("/v1/generate/opener", request)

    def generate_reply(
        self,
        profile: MatchProfile,
        last_messages: Optional[List[Message]] = None
    ) -> MessageResponse:
        # return MessageResponse(message="Hello, I am a bot REPLY")
        """Generate a reply based on previous messages"""
        request = ReplyRequest(
            profile=profile,
            last_messages=last_messages
        )
        return self._make_request("/v1/generate/reply", request)


class MockMessengerService(BaseMessengerService):
    """A fallback implementation of the Messenger Service."""
    def generate_opener(self, profile: MatchProfile) -> MessageResponse:
        """Generate a default opening message."""
        return MessageResponse(message=f"Hi {profile.name} 😊!")

    def generate_reply(
        self,
        profile: MatchProfile,
        last_messages: Optional[List[Message]] = None
    ) -> MessageResponse:
        """Generate an empty reply."""
        raise NotImplementedError("Reply is not implemented")

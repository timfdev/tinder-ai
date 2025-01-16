import asyncio
import httpx
from shared.models import (
    Message,
    MatchProfile,
    OpeningMessageRequest,
    ReplyRequest
)


API_BASE_URL = "http://localhost:8080/v1/generate"


async def test_generate_opener():
    """
    Test the /v1/generate/opener endpoint.
    """
    profile = MatchProfile(
        match_id="12345",
        name="Alex",
        age=29,
        bio="Love hiking and exploring new places.",
        interests=["hiking", "traveling", "photography"],
        looking_for="Someone adventurous",
        location="San Francisco",
        distance="5 miles",
        essentials=["Non-smoker", "Dog lover"],
        lifestyle={"diet": "Vegetarian", "exercise": "Regular"},
    )

    request_payload = OpeningMessageRequest(profile=profile)
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE_URL}/opener", json=request_payload.dict())
        print("Opener Response:", response.json())


async def test_generate_reply():
    """
    Test the /v1/generate/reply endpoint.
    """
    profile = MatchProfile(
        match_id="12345",
        name="Alex",
        age=29,
        bio="Love hiking and exploring new places.",
        interests=["hiking", "traveling", "photography"],
        looking_for="Someone adventurous",
        location="San Francisco",
        distance="5 miles",
        essentials=["Non-smoker", "Dog lover"],
        lifestyle={"diet": "Vegetarian", "exercise": "Regular"},
    )

    last_messages = [
        Message(message="Hey Alex! I see you're into hiking. What's your favorite trail?", is_received=True),
        Message(message="Hi! I love Mission Peak. It's challenging but worth it for the view.", is_received=False),
    ]

    request_payload = ReplyRequest(profile=profile, last_messages=last_messages)
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE_URL}/reply", json=request_payload.dict())
        print("Reply Response:", response.json())


async def main():
    print("Testing /v1/generate/opener...")
    await test_generate_opener()

    print("\nTesting /v1/generate/reply...")
    await test_generate_reply()


if __name__ == "__main__":
    asyncio.run(main())

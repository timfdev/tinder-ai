from messenger.app.src.agents import DatingAgent
from shared.models import MatchProfile, Message
import asyncio
from typing import List
from messenger.app.db.database import reset_db
from messenger.app.src.profiles import personal_profile
from shared.exceptions import MatchReadyException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestProfile:
    def __init__(
        self,
        profile: MatchProfile,
        messages: List[str]
    ):
        self.profile = profile
        self.messages = messages


# Test matches with their conversation styles
annemijn_test = TestProfile(
    profile=MatchProfile(
        match_id="test_match1",
        name="Annemijn",
        age=26,
        bio="Better in person 💃",
        interests=["Spa", "Sushi", "Brunch", "Music"],
        looking_for="Long-term partner",
        lifestyle={
            "Pets": "Cat",
            "Drinking": "On Special Occasions",
            "Smoking": "Non-Smoker",
            "Workout": "Sometimes",
            "Diet": "Omnivore",
            "Social-media": "Passive scroller"
        }
    ),
    messages=[
        "Hi 😊",
        "Haha, where r u from?",
        "Oh I was actually born in the US but grew up in KL. How about you?",
        "Oh, ur here for a visit? Want me to show you around KL? :p",
    ]
)

sarah_test = TestProfile(
    profile=MatchProfile(
        match_id="test_match2",
        name="Sarah",
        age=29,
        bio="Wine > Whine 🍷",
        interests=["Yoga", "Wine", "Travel", "Food"],
        looking_for="Something casual",
        lifestyle={
            "Pets": "Dog person",
            "Drinking": "Social drinker",
            "Smoking": "Non-Smoker",
            "Workout": "Regular",
            "Diet": "Flexitarian",
            "Social-media": "Instagram lover"
        }
    ),
    messages=[
        "Heya 💁‍♀️",
        "omg same! which area r u in?",
        "no way, im in bangsar too!",
        "we should grab a drink there sometime 😉",
    ]
)


lisa_test = TestProfile(
    profile=MatchProfile(
        match_id="test_match3",
        name="Lisa",
        age=23,
        bio="Here for a good time not a long time 😈",
        interests=["Clubbing", "Cocktails", "Beach", "Dancing"],
        looking_for="Let's see what happens",
        lifestyle={
            "Pets": "None",
            "Drinking": "Yes please!",
            "Smoking": "Social smoker",
            "Workout": "Gym bunny",
            "Diet": "Everything",
            "Social-media": "Influencer"
        }
    ),
    messages=[
        "hey u 😊",
        "hahah love ur bio! u party?",
        "omgg we should hit up zouk sometime! have u been?",
        "this weekend mayb? 💃",
    ]
)


async def test_conversation(test_match: TestProfile):
    logger.info(f"\nTesting conversation with {test_match.profile.name}")
    logger.info("=" * 50)

    agent = DatingAgent(personal_profile=personal_profile)
    try:
        async with agent:
            # Test opening message
            response = await agent.handle_message(
                match_id=test_match.profile.match_id,
                profile=test_match.profile
            )
            logger.info(f"Opening message: {response}\n")

            # Test responses to their messages
            for msg in test_match.messages:
                logger.info(f"{test_match.profile.name}: {msg}")
                response = await agent.handle_message(
                    match_id=test_match.profile.match_id,
                    profile=test_match.profile,
                    messages=[
                        Message(message=msg, is_received=True)
                    ]
                )
                logger.info(f"Agent: {response}\n")
    except MatchReadyException:
        logger.info("Match is ready to meet!")


async def run_tests():
    # Test different matches
    for test_match in [annemijn_test, sarah_test, lisa_test]:
        await test_conversation(test_match)

if __name__ == "__main__":
    reset_db()
    asyncio.run(run_tests())
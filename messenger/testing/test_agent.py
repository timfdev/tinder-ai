import logging
import asyncio
from messenger.app.src.agents import DatingAgent
from shared.models import MatchProfile, Message
from messenger.app.src.profiles import personal_profile
from shared.exceptions import MatchReadyException

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_dating_agent():
    """
    Extended test to demonstrate multiple message exchanges
    with the DatingAgent.
    """

    # Random Tinder profile
    profile = MatchProfile(
        match_id="12345",
        name="Annemijn",
        age=29,
        bio="Looking for someone to explore the city with 🍷 \nBig fan of cozy wine bars and Sunday brunches. My dog Charlie approves all my dates 🐕",
        interests=["wine tasting", "brunch spots", "city walks", "live music", "trying new restaurants"],
        looking_for="Something real, but let's see how it goes 😊",
        location="Kuala Lumpur",
        distance="10 km",
        essentials=["Dog lover", "Non-smoker", "Drinks socially"],
        lifestyle={"exercise": "Gym & walks with Charlie", "diet": "Foodie"}
    )

    try:
        # Initialize agent
        async with DatingAgent(
            personal_profile=personal_profile, verbose=True
        ) as agent:

            # Generate opener
            logger.info("Generating opener...")
            await agent.handle_message(
                match_id=profile.match_id,
                profile=profile
            )

            messages = [
                "Hey Tim! Thanks for the like 😊",

                "Thanks! I love discovering new wine spots - any favorites around KL? I've just moved here actually 🍷",

                "Same here with Charlie! 🐕 I usually hang around KLCC area for our walks, but still exploring. Where do you usually go?",

                "omg have you tried Dr.Inc in Bangsar? Such a cute wine bar! They're super dog friendly too, Charlie loves it there 🐾🍷",

                "Perfect! Would love to check it out - Charlie and I are free Saturday evening if you'd like to join? 😊🐕",
            ]

            # Send messages
            for i, message_text in enumerate(messages, 1):
                logger.info(f"\nSending user message {i}: {message_text}")
                user_message = Message(
                    message=message_text,
                    is_received=True
                )
                try:
                    await agent.handle_message(
                        match_id=profile.match_id,
                        profile=profile,
                        message=user_message
                    )
                except MatchReadyException:
                    break

            logger.info("\nFinal Conversation State:")
            state = agent.conversations[profile.match_id]
            logger.info(f"Number of Messages: {len(state.messages)}")
            logger.info(f"Memory Messages: {len(state.memory.chat_memory.messages)}")
            logger.info(f"Last Interaction: {state.last_interaction}")

    except Exception as e:
        logger.error(f"{str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(test_dating_agent())
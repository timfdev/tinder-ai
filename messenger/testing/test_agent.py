import logging
import asyncio
from messenger.app.src.agent import DatingAgent
from shared.models import MatchProfile, Message
from messenger.app.src.profiles import personal_profile

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_dating_agent():
    """
    Extended test to demonstrate
    multiple message exchanges with the DatingAgent.
    """

    # Sample user profile
    profile = MatchProfile(
        match_id="12345",
        name="Alex",
        age=29,
        bio="Love hiking and exploring new places.",
        interests=["hiking", "photography"],
        looking_for="Adventurous partner",
        location="New York",
        distance="10 miles",
        essentials=["Dog lover", "Non-smoker"],
        lifestyle={"diet": "Vegetarian", "exercise": "Regular"}
    )

    try:
        # Initialize agent with your personal (main) profile
        agent = DatingAgent(personal_profile=personal_profile)

        # 1) Generate an opener (no user message yet)
        logger.info("Generating opener...")
        await agent.handle_message(
            match_id=profile.match_id,
            profile=profile
        )

        user_message1 = Message(
            "I love hiking too! What's your favorite trail?",
            is_received=True
        )
        logger.info(
            f"Sending user message: {user_message1.message}"
        )
        # 2) User responds about hiking
        logger.info("\nSimulating user response 1...")
        user_message1 = Message(
            message=user_message1,
            is_received=True
        )
        await agent.handle_message(
            match_id=profile.match_id,
            profile=profile,
            message=user_message1
        )

        # 3) User asks a follow-up about photography
        user_message2 = Message(
            "That's cool! Do you also enjoy nature photography?",
            is_received=True
        )
        logger.info(
            f"Sending user message: {user_message2.message}"
        )
        user_message2 = Message(
            message=user_message2,
            is_received=True
        )
        await agent.handle_message(
            match_id=profile.match_id,
            profile=profile,
            message=user_message2
        )

        # 4) Another user turn, maybe mentioning coffee
        user_message3 = Message(
            "I'm also a huge coffee lover—any favorite coffee spots in the city?",
            is_received=True
        )
        logger.info(
            f"Sending user message: {user_message3.message}"
        )
        await agent.handle_message(
            match_id=profile.match_id,
            profile=profile,
            message=user_message3
        )

        # 5) User hints at meeting up
        user_message4 = Message(
            "We should totally grab a coffee sometime! I'd love to hear more about your hiking adventures!",
            is_received=True
        )
        logger.info(
            f"Sending user message: {user_message4.message}"
        )
        await agent.handle_message(
            match_id=profile.match_id,
            profile=profile,
            message=user_message4
        )

        # Show final conversation state (if desired)
        logger.info("\nFinal Conversation State:")
        state = agent.conversations[profile.match_id]
        logger.info(f"Meeting Readiness Score: {state.meeting_readiness_score}")
        logger.info(f"Number of Messages: {len(state.messages)}")
        logger.info(f"Last Interaction: {state.last_interaction}")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_dating_agent())

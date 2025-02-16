from tinder_ai.session import Session
from tinder_ai.services.messenger_api import (
    MockMessengerService,
    MessengerService
)
from tinder_ai.settings import Settings
from tinder_ai.utils import configure_logger, BANNER

import argparse
import logging

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description=(
            "A bot manager for Tinder automation."
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    parser.add_argument(
        '--mock',
        action='store_true',
        help=(
            "Enable mock mode for messenger service. "
            "Messenger API requests will be made "
            "but no messages will be sent"
        )
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--messages',
        action='store_true',
        help='Only handle unread messages'
    )
    group.add_argument(
        '--matches',
        action='store_true',
        help='Only handle new matches'
    )
    group.add_argument(
        '--swipe',
        action='store_true',
        help='Only automate swiping'
    )
    group.add_argument(
        '--all',
        action='store_true',
        help='Run all automation tasks'
    )

    args = parser.parse_args()
    if not any([args.messages, args.matches, args.swipe, args.all]):
        parser.print_help()
        parser.exit()

    return args


def run_all_tasks(session, duration=30 * 60):
    import time
    """Run all tasks for the specified duration (default: 30 minutes)."""
    start_time = time.time()  # Record the start time
    logger.info("Starting all tasks for 30 minutes...")

    while time.time() - start_time < duration:
        # Step 1: Swipe (finite amount)
        logger.info("Starting swiping...")
        session.start_swiping()

        # Step 2: Alternate between handling matches and messages
        while True:
            logger.info("Handling matches...")
            session.handle_matches()

            logger.info("Handling unread messages...")
            session.handle_unread_messages()

            # Check if 30 minutes have passed after each cycle
            if time.time() - start_time >= duration:
                logger.info("Time's up! Ending all tasks.")
                return  # Exit the function

            # Optional: Add a small delay between cycles (e.g., 5 seconds)
            time.sleep(5)


def main():
    """Main entry point"""

    args = parse_args()
    settings = Settings()

    configure_logger(level=logging.DEBUG if args.debug else logging.INFO)
    logger.info(
        BANNER
    )

    if api := settings.get_messenger_api():
        messenger_service = MessengerService(
            base_url=api
        )
    else:
        messenger_service = MockMessengerService()

    with Session(
        settings=settings,
        persist_user_data=True,
        mock=args.mock,
        messenger_service=messenger_service
    ) as session:
        try:
            # Login
            logger.info("Logging in...")
            session.login(
                method=settings.get_login_method()
            )

            if args.messages:
                logger.info("Handling unread messages...")
                session.handle_unread_messages()

            elif args.matches:
                logger.info("Handling new matches...")
                session.handle_matches()

            elif args.swipe:
                logger.info("Starting auto-swipe...")
                session.start_swiping()

            elif args.all:
                # Create your own logic here
                logger.info("Running all tasks...")
                # session.handle_matches()
                run_all_tasks(session)

        except Exception as e:
            logger.error(f"Error during execution: {e}")
            raise


if __name__ == "__main__":
    main()

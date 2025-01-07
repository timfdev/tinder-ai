from bot.src.session import Session
from bot.src.services.messenger_api import MessengerService
from bot.src.settings import Settings
from bot.src.utils.logger import configure_logger
import argparse
import time
import logging

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description=(
            "╔═══════════════════════════════╗\n"
            "║          AgentTinder          ║\n"
            "║                               ║\n"
            "║ GitHub:                       ║\n"
            "║    https://github.com/timfdev ║\n"
            "╚═══════════════════════════════╝"
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
            "No messenger API requests will be made "
            "and no messages will be sent"
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


def main():
    """Main entry point"""

    # Parse command line arguments
    args = parse_args()

    # Configure logger
    configure_logger(level=logging.DEBUG if args.debug else logging.INFO)

    # Load settings
    settings = Settings()

    # Create session instance
    with Session(
        settings=settings,
        persist_user_data=True,
        messenger_service=MessengerService(
            "http://localhost:8000", mock=True
        )
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
                logger.info("Running all automation tasks...")
                session.handle_matches()
                session.handle_unread_messages()
                time.sleep(2)
                session.start_swiping()

        except Exception as e:
            logger.error(f"Error during execution: {e}")
            raise


if __name__ == "__main__":
    main()

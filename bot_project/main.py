

from bot.session import Session
from bot.constants.models import (
    LoginMethods,
)
from bot.settings import Settings
from bot.utils.logger import configure_logger
from pathlib import Path
import time

if __name__ == "__main__":
    # Configure logger
    configure_logger()

    # Load settings
    settings = Settings()

    # creates instance of session
    with Session(
        settings=settings,
        user_data=Path("user_data")
    ) as session:
        session.login(LoginMethods.FACEBOOK)
        # session.set_preferences()
        session.handle_matches()
        time.sleep(2000)
        session.start_swiping()

    exit()

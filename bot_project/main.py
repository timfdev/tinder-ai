

from bot.session import Session
from bot.constants.models import (
    LoginMethods,
)
from bot.settings import Settings


if __name__ == "__main__":
    # Load settings
    settings = Settings()

    # creates instance of session
    with Session(settings=settings, use_local_proxy_server=True) as session:
        session.login(LoginMethods.FACEBOOK)
        session.set_preferences()
        session.start_swiping()

    exit()

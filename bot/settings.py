from pydantic import Field
from pydantic_settings import BaseSettings
from bot.constants.models import Sexuality
from typing import Optional
from bot.constants.models import LoginMethods


class Settings(BaseSettings):
    # Login Credentials
    facebook_email: Optional[str] = Field(None, env="FACEBOOK_EMAIL")
    facebook_password: Optional[str] = Field(None, env="FACEBOOK_PASSWORD")

    google_email: Optional[str] = Field(None, env="FACEBOOK_EMAIL")
    google_password: Optional[str] = Field(None, env="FACEBOOK_PASSWORD")

    # Messenger Service
    messenger_api: Optional[str] = Field(None, env="MESSENGER_API")

    # Proxy Configuration
    proxy_url: Optional[str] = Field(None, env="PROXY_URL")

    # Tinder Preferences
    age_range_min: int = Field(18, env="AGE_RANGE_MIN")
    age_range_max: int = Field(28, env="AGE_RANGE_MAX")
    location_lat: Optional[float] = Field(None, env="LOCATION_LAT")
    location_lon: Optional[float] = Field(None, env="LOCATION_LON")
    distance_range: int = Field(50, env="DISTANCE_RANGE")
    gender_preference: Sexuality = Field(
        Sexuality.EVERYONE, env="GENDER_PREFERENCE"
    )
    set_global: bool = Field(False, env="SET_GLOBAL")

    # Bot Behavior
    swipe_limit: int = Field(100, env="SWIPE_LIMIT")

    def get_login_method(self) -> LoginMethods:
        """Determine login method based on available credentials"""
        if self.facebook_email and self.facebook_password:
            return LoginMethods.FACEBOOK
        elif self.google_email and self.google_password:
            return LoginMethods.GOOGLE
        raise ValueError("No valid login credentials found in settings")

    def get_messenger_api(self) -> Optional[str]:
        """" Return the given messenger service base url """
        if self.messenger_api:
            return self.messenger_api
        return None

    class Config:
        env_file = ".env"

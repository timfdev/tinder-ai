from pydantic import Field
from pydantic_settings import BaseSettings
from bot.constants.models import Sexuality
from typing import Optional


class Settings(BaseSettings):
    # Login Credentials
    facebook_email: str = Field(..., env="FACEBOOK_EMAIL")  # Required
    facebook_password: str = Field(..., env="FACEBOOK_PASSWORD")  # Required

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

    class Config:
        env_file = ".env"

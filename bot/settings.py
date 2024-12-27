from pydantic import Field
from pydantic_settings import BaseSettings
from bot.constants.models import Sexuality, Proxy
from typing import Optional


class Settings(BaseSettings):
    # Login Credentials
    facebook_email: str = Field(..., env="FACEBOOK_EMAIL")  # Required
    facebook_password: str = Field(..., env="FACEBOOK_PASSWORD")  # Required

    # Proxy Configuration
    proxy_host: Optional[str] = Field(None, env="PROXY_HOST")
    proxy_port: Optional[int] = Field(None, env="PROXY_PORT")
    proxy_user: Optional[str] = Field(None, env="PROXY_USER")
    proxy_pass: Optional[str] = Field(None, env="PROXY_PASS")

    # Tinder Preferences
    age_range_min: int = Field(18, env="AGE_RANGE_MIN")  # Default: 18
    age_range_max: int = Field(100, env="AGE_RANGE_MAX")  # Default: 100
    location_lat: Optional[float] = Field(None, env="LOCATION_LAT")
    location_lon: Optional[float] = Field(None, env="LOCATION_LON")
    distance_range: int = Field(50, env="DISTANCE_RANGE")  # Default: 50 km
    gender_preference: Sexuality = Field(Sexuality.EVERYONE, env="GENDER_PREFERENCE")  # Default: everyone

    # Bot Behavior
    daily_swipe_limit: int = Field(100, env="DAILY_SWIPE_LIMIT")  # Default: 100 swipes
    swipe_delay_min: int = Field(2, env="SWIPE_DELAY_MIN")  # Default: 2 seconds
    swipe_delay_max: int = Field(5, env="SWIPE_DELAY_MAX")  # Default: 5 seconds

    class Config:
        env_file = ".env"

    @property
    def proxy(self) -> Proxy:
        return Proxy(
            host=self.proxy_host,
            port=self.proxy_port,
            user=self.proxy_user,
            pwd=self.proxy_pass
        )
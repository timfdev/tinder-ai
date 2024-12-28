from bot.settings import Settings

# Load settings from .env file
settings = Settings()
print(settings)
print()
print(f"Proxy: {settings.proxy}")
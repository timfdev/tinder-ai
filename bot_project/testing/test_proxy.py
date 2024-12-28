from bot.session import Session
from bot.settings import Settings
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load environment variables
settings = Settings()

try:
    with Session(settings=settings, use_local_proxy_server=True) as session:
        # Open an IP-checking website
        session.browser.get("https://www.whatismyip.com")
        WebDriverWait(session.browser, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5000)

except Exception as e:
    print(f"Error occurred: {e}")

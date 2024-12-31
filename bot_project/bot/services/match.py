from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from logging import getLogger

logger = getLogger(__name__)


class MatchService:
    def __init__(self, browser):
        """
        Initialize the Matcher class.
        :param browser: The browser instance used for interaction.
        """
        self.browser = browser

    def like(self):
        """
        Attempt to like the profile currently on the screen using ActionChains.
        :return: True if successful, False otherwise.
        """
        try:
            like_button_xpath = (
                "//button[contains(@class, 'gamepad-button')]"
                "[.//span[contains(@class, 'Hidden') and text()='Like']]"
            )
            like_button = WebDriverWait(self.browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, like_button_xpath))
            )

            actions = ActionChains(self.browser)
            actions.move_to_element(like_button).click().perform()
            return True
        except NoSuchElementException:
            logger.info("Like button not found.")
        except Exception as e:
            import traceback
            logger.info(f"Error occurred while liking: {e}")
            logger.info(traceback.format_exc())
        return False

    def dislike(self):
        """
        Attempt to dislike the profile currently on the screen using ActionChains.
        :return: True if successful, False otherwise.
        """
        try:
            # Find the button with text "Nope" inside <span class="Hidden">Nope</span>
            # (If the actual text is different, adjust accordingly.)
            dislike_button_xpath = (
                "//button[contains(@class, 'gamepad-button')]"
                "[.//span[contains(@class, 'Hidden') and (text()='Nope' or text()='No')]]"
            )
            dislike_button = WebDriverWait(self.browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, dislike_button_xpath))
            )

            actions = ActionChains(self.browser)
            actions.move_to_element(dislike_button).click().perform()
            return True
        except NoSuchElementException:
            logger.info("Dislike button not found.")
        except Exception as e:
            logger.info(f"Error occurred while disliking: {e}")
        return False
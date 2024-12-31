from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


class Matcher:
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
            # Find the button with text "Like" inside <span class="Hidden">Like</span>
            like_button_xpath = (
                "//button[contains(@class, 'gamepad-button')]"
                "[.//span[contains(@class, 'Hidden') and text()='Like']]"
            )
            like_button = WebDriverWait(self.browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, like_button_xpath))
            )

            # Use ActionChains to hover and then click
            actions = ActionChains(self.browser)
            actions.move_to_element(like_button).click().perform()

            print("Profile liked successfully.")
            return True
        except NoSuchElementException:
            print("Like button not found.")
        except Exception as e:
            import traceback
            print(f"Error occurred while liking: {e}")
            print(traceback.format_exc())
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

            print("Profile disliked successfully.")
            return True
        except NoSuchElementException:
            print("Dislike button not found.")
        except Exception as e:
            print(f"Error occurred while disliking: {e}")
        return False

    def _handle_popups(self):
        """
        Handle any popups that might appear during interaction.
        """
        try:
            # Example: if there's a close button
            popup_close_button_xpath = "//button[contains(@aria-label, 'Close')]"
            popup_close_button = WebDriverWait(self.browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, popup_close_button_xpath))
            )
            popup_close_button.click()
            print("Popup closed successfully.")
        except NoSuchElementException:
            # No popup found; do nothing
            pass
        except Exception as e:
            print(f"Error occurred while handling popup: {e}")

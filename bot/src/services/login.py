from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    NoSuchElementException,
    NoSuchWindowException
)
from selenium.webdriver.common.keys import Keys
import time
from logging import getLogger
from selenium.webdriver.common.action_chains import ActionChains


logger = getLogger(__name__)


class LoginService:
    WEBDRIVER_WAIT_TIME = 10

    def __init__(self, browser):
        self.browser = browser
        self.main_window_handle = self.browser.current_window_handle
        self._accept_cookies()

    def _click_login_button(self):
        try:
            xpath = "//a[contains(., 'Log in')]"

            wait = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME)
            button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

            # Ensure the button is displayed before interacting
            if button.is_displayed():
                actions = ActionChains(self.browser)
                actions.move_to_element(button).click().perform()
                logger.info("Login button clicked successfully!")
                time.sleep(3)
            else:
                logger.warning("Login button is not displayed.")

        except TimeoutException:
            logger.error("Timeout while waiting for the login button.")
            raise

        except ElementClickInterceptedException:
            logger.warning("ElementClickInterceptedException occurred while clicking the login button.")

    def login_by_google(self, email, password):
        logger.info("Logging in with Google...")
        self._click_login_button()

        # Wait for Google login button and click
        try:
            xpath = '//*[@aria-label="Log in with Google"]'
            google_button = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            actions = ActionChains(self.browser)
            actions.move_to_element(google_button).click().perform()
            logger.info("Clicked Google login button.")
        except TimeoutException:
            logger.error("Timeout while waiting for Google login button.")
            raise

        # Switch to the popup
        if not self._change_focus_to_pop_up():
            logger.error("Failed to switch focus to Google popup.")
            return False

        # Handle Google login flow
        try:
            # Enter email
            email_xpath = "//input[@type='email']"
            email_field = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, email_xpath))
            )
            email_field.send_keys(email)
            email_field.send_keys(Keys.ENTER)
            logger.info("Entered email and proceeded.")

            # Wait for password field
            password_xpath = "//input[@type='password']"
            password_field = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, password_xpath))
            )
            password_field.send_keys(password)
            password_field.send_keys(Keys.ENTER)
            logger.info("Entered password and proceeded.")

        except TimeoutException:
            logger.error("Timeout during Google login flow.")
            raise
        except Exception as e:
            logger.error(f"Error during Google login: {e}")
            raise

        # Switch back to the main window
        self._change_focus_to_main_window()
        logger.info("Switched focus back to the main window.")
        return True

    def login_by_facebook(self, email, password):
        logger.info("Logging in with Facebook...")
        self._click_login_button()

        # Wait for Facebook login button
        try:
            xpath = '//*[@aria-label="Log in with Facebook"]'
            facebook_button = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            actions = ActionChains(self.browser)
            actions.move_to_element(facebook_button).click().perform()
            logger.info("Clicked Facebook login button.")
        except TimeoutException:
            logger.error("Timeout while waiting for Facebook login button.")
            raise

        # Switch to the popup
        if not self._change_focus_to_pop_up():
            return False

        if not self._click_continue_as():
            logger.info("Attempting manual login.")
            try:
                xpath_email = '//*[@id="email"]'
                xpath_password = '//*[@id="pass"]'
                xpath_button = '//*[@id="loginbutton"]'

                email_field = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                    EC.presence_of_element_located((By.XPATH, xpath_email))
                )
                email_field.send_keys(email)

                password_field = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                    EC.presence_of_element_located((By.XPATH, xpath_password))
                )
                password_field.send_keys(password)

                login_button = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                    EC.element_to_be_clickable((By.XPATH, xpath_button))
                )
                login_button.click()
                logger.info("Manual email/password login successful.")
                self._click_continue_as()
            except TimeoutException:
                logger.error("Timeout occurred during manual Facebook login.")
                raise

        # Switch back to the main window
        self._change_focus_to_main_window()
        return True

    def _accept_cookies(self):
        try:
            xpath = '//*[@type="button"]'
            WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            buttons = self.browser.find_elements(By.XPATH, xpath)
            for button in buttons:
                try:
                    # Check text inside <span> or directly inside button
                    try:
                        text_span = button.find_element(By.XPATH, './/span').text
                    except NoSuchElementException:
                        text_span = button.text  # Fallback to button's direct text

                    button_html = button.get_attribute('outerHTML')
                    if 'accept' in text_span.lower() or 'i accept' in button_html.lower():
                        button.click()
                        logger.info("COOKIES ACCEPTED.")
                        time.sleep(1.5)
                        break
                except NoSuchElementException:
                    pass

        except TimeoutException:
            logger.info(
                "ACCEPTING COOKIES: Loading took too much time! Element probably not present, so we continue."
            )
        except Exception as e:
            logger.info("Error while accepting cookies:", e)

    def _click_continue_as(self):
        try:
            xpath_continue = '//div[starts-with(@aria-label, "Continue as")]'
            continue_button = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, xpath_continue))
            )
            ActionChains(self.browser).move_to_element(continue_button).click().perform()
            logger.info("Clicked 'Continue as' button.")
        except TimeoutException:
            logger.info("'Continue as' button not found.")

    def _change_focus_to_pop_up(self):
        main_window = self.browser.current_window_handle
        for _ in range(50):  # Retry mechanism
            handles = self.browser.window_handles
            for handle in handles:
                if handle != main_window:
                    self.browser.switch_to.window(handle)
                    logger.info(f"Switched to popup window: {handle}")

                    # Ensure popup is loaded
                    WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                        lambda driver: "facebook" in driver.current_url or "google" in driver.current_url
                    )
                    return True
            time.sleep(0.3)

        logger.error("Popup window not found.")
        return False

    def _change_focus_to_main_window(self):
        try:
            self.browser.switch_to.window(self.main_window_handle)
            logger.info("Switched back to the main window.")
        except NoSuchWindowException:
            logger.error("Main window is no longer available.")



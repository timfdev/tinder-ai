from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
    NoSuchWindowException
)
from selenium.webdriver.common.keys import Keys
import time
from logging import getLogger
from selenium.webdriver.common.action_chains import ActionChains


logger = getLogger(__name__)


class LoginService:
    """
    A service class to handle login operations
    for a web application using Selenium WebDriver.

    Attributes:
        WEBDRIVER_WAIT_TIME (int):
            The maximum wait time for web elements to be interactable.
        browser (WebDriver):
            The Selenium WebDriver instance.
        main_window_handle (str):
            The handle of the main browser window.
    """
    WEBDRIVER_WAIT_TIME = 10

    def __init__(self, browser) -> None:
        self.browser = browser
        self.main_window_handle = self.browser.current_window_handle
        self._accept_cookies()

    def _click_login_button(self) -> None:
        """
        Attempts to click the login button on the webpage.

        This method waits for the login button to become clickable,
        ensures it is displayed,
        and then performs a click action.
        If the button is not displayed or if there is a
        timeout while waiting for the button,
        appropriate warnings or errors are logged.

        Raises:
            TimeoutException:
                If the login button is not clickable within
                the specified wait time.
            ElementClickInterceptedException:
                If an error occurs while attempting to click the login button.
        """
        try:
            xpath = "//a[contains(., 'Log in')]"

            wait = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME)
            button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

            # Ensure the button is displayed before interacting
            if button.is_displayed():
                actions = ActionChains(self.browser)
                actions.move_to_element(button).click().perform()
                logger.info("Login button clicked successfully!")
            else:
                logger.warning("Login button is not displayed.")

        except TimeoutException:
            logger.error("Timeout while waiting for the login button.")
            raise

        except ElementClickInterceptedException as e:
            logger.warning(
                f"{e} occurred while clicking the login button."
            )

    def login_by_google(self, email, password) -> bool:
        """
        Logs in to the application using Google authentication.

        Args:
            email (str): The email address to use for Google login.
            password (str): The password associated with the Google account.

        Returns:
            bool: True if login was successful, False otherwise.

        Raises:
            TimeoutException:
                If an element is not found within the specified wait time.
            Exception:
                For any other errors that occur during the login process.
        """
        logger.info("Logging in with Google...")
        self._click_login_button()

        try:
            xpath = '//*[@aria-label="Log in with Google"]'
            google_button = WebDriverWait(
                self.browser, self.WEBDRIVER_WAIT_TIME
            ).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            actions = ActionChains(self.browser)
            actions.move_to_element(google_button).click().perform()
            logger.info("Clicked Google login button.")
        except TimeoutException:
            logger.error("Timeout while waiting for Google login button.")
            raise

        if not self._change_focus_to_pop_up():
            logger.error("Failed to switch focus to Google popup.")
            return False

        try:
            email_xpath = "//input[@type='email']"
            email_field = WebDriverWait(
                self.browser, self.WEBDRIVER_WAIT_TIME
            ).until(
                EC.presence_of_element_located((By.XPATH, email_xpath))
            )
            email_field.send_keys(email)
            email_field.send_keys(Keys.ENTER)
            logger.info("Entered email and proceeded.")

            password_xpath = "//input[@type='password']"
            password_field = WebDriverWait(
                self.browser, self.WEBDRIVER_WAIT_TIME
            ).until(
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

    def login_by_facebook(self, email, password) -> bool:
        """
        Logs into the application using Facebook credentials.

        This method attempts to log in using Facebook
        by clicking the Facebook login button,
        switching to the Facebook login popup, and either clicking
        the "Continue as" button
        or manually entering the email and password if
        the "Continue as" button is not available.

        Args:
            email (str):
                The email address associated with the Facebook account.
            password (str):
                The password associated with the Facebook account.

        Returns:
            bool: True if the login was successful, False otherwise.

        Raises:
            TimeoutException:
                If any of the required elements are not
                found within the specified wait time.
        """
        logger.info("Logging in with Facebook...")
        self._click_login_button()

        # Wait for Facebook login button
        try:
            xpath = '//*[@aria-label="Log in with Facebook"]'
            facebook_button = WebDriverWait(
                self.browser, self.WEBDRIVER_WAIT_TIME
            ).until(
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

                email_field = WebDriverWait(
                    self.browser, self.WEBDRIVER_WAIT_TIME
                ).until(
                    EC.presence_of_element_located((By.XPATH, xpath_email))
                )
                email_field.send_keys(email)

                password_field = WebDriverWait(
                    self.browser, self.WEBDRIVER_WAIT_TIME
                ).until(
                    EC.presence_of_element_located((By.XPATH, xpath_password))
                )
                password_field.send_keys(password)

                login_button = WebDriverWait(
                    self.browser, self.WEBDRIVER_WAIT_TIME
                ).until(
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

    def _accept_cookies(self) -> None:
        """
        Attempts to accept cookies on a webpage by
        clicking the appropriate button.

        This method waits for buttons to be clickable,
        then iterates through them to find
        one that either has a span element with text
        indicating acceptance or has HTML
        content suggesting it is an accept button.
        If found, the button is clicked to accept cookies.

        Exceptions:
            - NoSuchElementException:
                If an element is not found during the process.
            - TimeoutException:
                If the buttons do not become clickable
                within the specified wait time.
            - Exception:
                For any other unexpected errors during the process.

        Logs:
            - Logs a message when cookies are successfully accepted.
            - Logs a message if the loading
              takes too much time and the element is not present.
            - Logs any other errors encountered during the process.
        """
        try:
            xpath = '//*[@type="button"]'
            WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            buttons = self.browser.find_elements(By.XPATH, xpath)
            for button in buttons:
                try:
                    try:
                        text_span = button.find_element(
                            By.XPATH, './/span'
                        ).text
                    except NoSuchElementException:
                        text_span = button.text

                    button_html = button.get_attribute('outerHTML')
                    if (
                        'accept' in text_span.lower()
                        or
                        'i accept' in button_html.lower()
                    ):
                        button.click()
                        logger.info("COOKIES ACCEPTED.")
                        break
                except NoSuchElementException:
                    pass

        except TimeoutException:
            logger.info(
                "ACCEPTING COOKIES: "
                "Loading took too much time! Element probably not present, "
                "so we continue."
            )
        except Exception as e:
            logger.info("Error while accepting cookies:", e)

    def _click_continue_as(self) -> None:
        """
        Attempts to click the "Continue as" button on the webpage.

        This method waits for the "Continue as" button to become
        clickable and then performs a click action on it.
        If the button is not found within the specified wait time,
        a TimeoutException is caught and logged.

        Raises:
            TimeoutException:
                If the "Continue as" button is not found
                within the specified wait time.
        """
        try:
            xpath_continue = '//div[starts-with(@aria-label, "Continue as")]'
            continue_button = WebDriverWait(
                self.browser, self.WEBDRIVER_WAIT_TIME
            ).until(
                EC.element_to_be_clickable((By.XPATH, xpath_continue))
            )
            ActionChains(
                self.browser
            ).move_to_element(continue_button).click().perform()
            logger.info("Clicked 'Continue as' button.")
        except TimeoutException:
            logger.info("'Continue as' button not found.")

    def _change_focus_to_pop_up(self) -> bool:
        """
        Attempts to change the browser's focus to a popup window.

        This method will retry up to 50 times, checking
        for any new window handles
        that are different from the main window handle.
        If a popup window is found,
        it switches to that window and waits until the URL contains
        either "facebook" or "google" to ensure the popup is fully loaded.

        Returns:
            bool:
                True if the focus was successfully changed to a popup window,
                False otherwise.
        """
        main_window = self.browser.current_window_handle
        for _ in range(50):  # Retry mechanism
            handles = self.browser.window_handles
            for handle in handles:
                if handle != main_window:
                    self.browser.switch_to.window(handle)
                    logger.info(f"Switched to popup window: {handle}")

                    # Ensure popup is loaded
                    WebDriverWait(
                        self.browser, self.WEBDRIVER_WAIT_TIME
                    ).until(
                        lambda driver: (
                            "facebook" in driver.current_url
                            or
                            "google" in driver.current_url
                        )
                    )
                    return True
            time.sleep(0.3)

        logger.error("Popup window not found.")
        return False

    def _change_focus_to_main_window(self) -> None:
        """
        Switches the browser's focus back to the main window.

        This method attempts to switch the browser's focus to the main window
        using the stored main window handle. If the main window is no longer
        available, it logs an error message.

        Raises:
            NoSuchWindowException: If the main window is no longer available.
        """
        try:
            self.browser.switch_to.window(self.main_window_handle)
            logger.info("Switched back to the main window.")
        except NoSuchWindowException:
            logger.error("Main window is no longer available.")



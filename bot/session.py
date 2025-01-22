import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementNotVisibleException,
    StaleElementReferenceException
)

import time
from bot.src.services.preferences import PreferencesService
from bot.src.services.login import LoginService
from bot.src.services.messenger_api import BaseMessengerService
from bot.src.constants.models import LoginMethods, SessionData
from bot.src.settings import Settings
from pathlib import Path
import random
from bot.src.services.match import Match
from bot.src.services.location import LocationService
from logging import getLogger
from typing import Literal, List
from shared.exceptions import MatchReadyException


logger = getLogger(__name__)


class Session:

    WEBDRIVER_WAIT_TIME = 10
    MIN_SLEEP = 1.1
    MAX_SLEEP = 2.6
    DEFAULT_WINDOW_SIZE = (1250, 750)

    def __init__(
        self,
        settings: Settings,
        messenger_service: BaseMessengerService,
        mock: bool = False,
        headless: bool = False,
        persist_user_data: bool = False
    ) -> None:
        """
        Initializes a session with support for a local proxy server.
        :param settings:
            Configuration settings containing proxy details.
        :type settings:
            Settings
        :param messenger_service:
            Service for handling messaging operations.
        :type messenger_service:
            BaseMessengerService
        :param headless:
            Run the browser in headless mode, defaults to False.
        :type headless:
            bool, optional
        :param persist_user_data:
            Persist user data across sessions, defaults to False.
        :type persist_user_data:
            bool, optional
        """
        self.session_data = SessionData()
        self.mock = mock
        self.start_session = time.time()

        options = uc.ChromeOptions()
        options.binary_location = "/usr/bin/google-chrome"
        options.add_argument("homepage=http://example.com")
        options.add_argument("--disable-notifications")
        options.add_argument(
            '--no-first-run --no-service-autorun --password-store=basic'
        )
        options.add_argument("--lang=en")
        options.add_argument("--disable-webrtc")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/112.0.5615.138"
            " Safari/537.36"
        )

        if persist_user_data:
            user_data_dir = Path(__file__).parent.parent / "user_data"
            options.add_argument(f"--user-data-dir={user_data_dir}")

        if settings.proxy_url is not None:
            # Use local proxy server
            logger.info(
                "Routing traffic through local proxy server: "
                f"{settings.proxy_url}"
            )
            options.add_argument(f"--proxy-server={settings.proxy_url}")

        if headless:
            options.headless = True

        # Allow geolocation by default
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.geolocation": 1
        })

        # Initialize the browser
        self.browser = uc.Chrome(options=options)

        self.browser.set_window_size(*self.DEFAULT_WINDOW_SIZE)
        self.settings = settings

        location_setter = LocationService(
            browser=self.browser,
            settings=self.settings
        )
        location_setter.configure_location()

        self.messenger_service = messenger_service

        self._random_sleep()

        self.started = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        logger.info(f"Started session: {self.started}\n\n")

    def __enter__(self) -> 'Session':
        return self

    def __exit__(self, *args, **kwargs) -> None:
        """Clean up when exiting context."""
        seconds = int(time.time() - self.start_session)
        self.session_data.duration = seconds

        logger.info(self.session_data)
        logger.info(
            "Ended session: "
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}"
        )

        self.browser.quit()

    def set_preferences(self) -> None:
        """
        Sets user preferences using the PreferencesService.

        This method initializes the PreferencesService
        with the current browser instance
        and applies the user settings to set preferences.

        Returns:
            None
        """
        PreferencesService(
            browser=self.browser
        ).set_preferences(settings=self.settings)

    def login(self, method: LoginMethods) -> None:
        """
        Logs in the user using the specified login method.

        Args:
            method (LoginMethods):
                The method to use for logging in.
                Can be either LoginMethods.FACEBOOK or LoginMethods.GOOGLE.

        Raises:
            ValueError:
                If the email or password for the
                specified login method is not set.
            Exception:
                If an unsupported login method is provided.

        Notes:
            - If the user is already logged in,
              the method will return immediately.
            - After attempting to log in,
              the method will check again if the user is logged in.
              If not, it will prompt the user to solve the captcha manually.
        """
        if self._is_logged_in():
            return

        login_service = LoginService(browser=self.browser)

        if method == LoginMethods.FACEBOOK:
            if not all(
                [self.settings.facebook_email,
                 self.settings.facebook_password]
            ):
                raise ValueError(
                    "Facebook email or password is not set. "
                    "Please provide valid credentials."
                )

            logger.info("Logging in using Facebook")
            login_service.login_by_facebook(
                self.settings.facebook_email,
                self.settings.facebook_password
            )
        elif method == LoginMethods.GOOGLE:
            if not all([
                self.settings.google_email,
                self.settings.google_password]
            ):
                raise ValueError(
                    "Google email or password is not set. "
                    "Please provide valid credentials."
                )

            logger.info("Logging in using Google")
            login_service.login_by_google(
                self.settings.google_email,
                self.settings.google_password
            )
        else:
            raise Exception("Unsupported login method")

        # After attempting to log in, check again
        if not self._is_logged_in():
            logger.warning('Unable to login, solve (the captcha) manually.')
            input('Press any key to continue')

    def start_swiping(self, ratio='90%') -> None:
        """
        Start liking or disliking profiles with a given ratio (e.g., '80%').
        """
        ratio_val = float(ratio.strip('%')) / 100

        if not self._is_logged_in():
            logger.warning(
                "Not logged in. "
                "Please log in before starting the liking process."
            )
            return

        logger.info("\nStarting to like profiles.")

        # Continue swiping until we hit our limit
        while self.session_data.likes < self.settings.swipe_limit:
            try:
                self._swipe_once(ratio_val)
                logger.info(
                    "Processed "
                    f"{self.session_data.likes}/"
                    f"{self.settings.swipe_limit} profiles."
                )
            except NoSuchElementException as e:
                logger.warning(f"Element not found: {e}. Retrying...")
                self.browser.refresh()
                time.sleep(self.WEBDRIVER_WAIT_TIME)
            except TimeoutException as e:
                logger.warning(f"Timeout encountered: {e}. Retrying...")
                self.browser.refresh()
                time.sleep(self.WEBDRIVER_WAIT_TIME)
            except Exception as e:
                logger.error(
                    f"Unexpected error occurred: {e}. Skipping this iteration."
                )

    def go_to_matches(self) -> None:
        """
        Navigate to the "Matches" tab.
        """
        try:
            # XPath for the "Matches" button
            matches_button_xpath = '//button[contains(text(), "Matches")]'

            # Wait for the button to be clickable
            matches_button = WebDriverWait(
                self.browser, self.WEBDRIVER_WAIT_TIME
            ).until(
                EC.element_to_be_clickable((By.XPATH, matches_button_xpath))
            )

            # Click the "Matches" button
            matches_button.click()
            logger.info("Navigated to the 'Matches' tab.")
        except TimeoutException:
            logger.error(
                "Timeout occurred while trying to navigate to 'Matches'."
            )
            raise
        except Exception as e:
            logger.error(
                f"An error occurred while navigating to 'Matches': {e}"
            )
            raise

    def go_to_messages(self) -> None:
        """
        Navigate to the "Messages" tab.
        """
        try:
            # XPath for the "Messages" button
            messages_button_xpath = '//button[contains(text(), "Messages")]'

            # Wait for the button to be clickable
            messages_button = WebDriverWait(
                self.browser, self.WEBDRIVER_WAIT_TIME
            ).until(
                EC.element_to_be_clickable((By.XPATH, messages_button_xpath))
            )

            # Click the "Messages" button
            messages_button.click()
            logger.info("Navigated to the 'Messages' tab.")
        except TimeoutException:
            logger.error(
                "Timeout occurred while trying to navigate to 'Messages'."
            )
            raise
        except Exception as e:
            logger.error(
                f"An error occurred while navigating to 'Messages': {e}"
            )
            self._handle_potential_popups()

    def handle_matches(self) -> None:
        """Handles all new matches."""
        self._handle_items(item_type='matches')

    def handle_unread_messages(self) -> None:
        """Handles all unread messages."""
        self._handle_items(item_type='unread_messages')

    def _is_logged_in(self) -> bool:
        """
        Checks if the user is logged into Tinder.

        This method verifies if the current URL of the
        browser contains "tinder.com".
        If not, it navigates to the Tinder homepage
        and waits until the URL contains "tinder.com".
        Then, it waits for the Tinder app page
        to load and confirms if the user is logged in.

        Returns:
            bool: True if the user is logged in, False otherwise.
        """
        if "tinder.com" not in self.browser.current_url:
            self.browser.get("https://tinder.com/?lang=en")
            try:
                WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                    EC.url_contains("tinder.com")
                )
            except TimeoutException:
                logger.info("Timeout while waiting for Tinder to load.")
                return False

        try:
            # Wait for the app page
            WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.url_contains("tinder.com/app")
            )
            logger.info("User is logged in.")
            return True
        except TimeoutException:
            logger.info(
                "User is not logged in yet. Current URL:\n "
                f"{self.browser.current_url}"
            )
            return False

    def _swipe_once(self, ratio_val: float) -> None:
        """
        Perform a single swipe iteration (like or dislike)
        with popups automatically handled before/after.
        """
        self._handle_potential_popups()
        like = random.random() <= ratio_val

        if like:
            if self._like():
                self.session_data.likes += 1
        else:
            if self._dislike():
                self.session_data.dislikes += 1

        self._random_sleep()
        self._handle_potential_popups()

    def _like(self) -> bool:
        """
        Attempt to like the profile currently on the screen.
        :return: True if successful, False otherwise.
        """
        try:
            like_button_xpath = (
                "//button[contains(@class, 'gamepad-button')]"
                "[.//span[contains(@class, 'Hidden') and text()='Like']]"
            )
            like_button = WebDriverWait(
                self.browser, self.WEBDRIVER_WAIT_TIME
            ).until(
                EC.element_to_be_clickable((By.XPATH, like_button_xpath))
            )

            actions = ActionChains(self.browser)
            actions.move_to_element(like_button).click().perform()
            return True
        except NoSuchElementException:
            logger.warning("Like button not found.")
        except Exception as e:
            logger.error(f"Error occurred while liking: {e}")
        return False

    def _dislike(self) -> bool:
        """
        Attempt to dislike the profile currently on the screen.
        :return: True if successful, False otherwise.
        """
        try:
            dislike_button_xpath = (
                "//button[contains(@class, 'gamepad-button')]"
                "[.//span[contains(@class, 'Hidden') and "
                "(text()='Nope' or text()='No')]]"
            )
            dislike_button = WebDriverWait(
                self.browser, self.WEBDRIVER_WAIT_TIME
            ).until(
                EC.element_to_be_clickable((By.XPATH, dislike_button_xpath))
            )

            actions = ActionChains(self.browser)
            actions.move_to_element(dislike_button).click().perform()
            return True
        except NoSuchElementException:
            logger.warning("Dislike button not found.")
        except Exception as e:
            logger.error(f"Error occurred while disliking: {e}")
        return False

    def _handle_items(
        self,
        item_type: Literal['matches', 'unread_messages']
    ) -> None:
        """
        Handle either 'matches' or 'unread_messages' in a single method.
        """

        self._random_sleep()
        self._handle_potential_popups()

        if item_type == 'matches':
            logger.info("Handling matches...")
            self.go_to_matches()
            self._handle_potential_popups()
            data_list = self._get_matches_data()
        else:
            logger.info("Handling unread messages...")
            self.go_to_messages()
            self._handle_potential_popups()
            data_list = self._get_unread_messages_data()

        self._random_sleep()

        logger.info(f"Found {len(data_list)} items to process")

        match_obj = None
        # Iterate over match/message data
        for index, item_id in enumerate(data_list[:10]):
            try:
                # Get the clickable element by ID
                match_selector = f"a[href*='{item_id}']"
                match_element = WebDriverWait(self.browser, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, match_selector))
                )

                if item_type == 'matches':
                    match_obj = Match.from_element(
                        match_element, self.browser
                    )
                else:
                    match_obj = Match.from_element(
                        match_element, self.browser, messages=True
                    )

                # Validatation
                if not match_obj.profile.name:
                    logger.warning(
                        "Could not extract data properly "
                        f"for {item_id}, skipping..."
                    )
                    continue

                logger.info(
                    f"Processing {index + 1} of {len(data_list)} "
                    f"- {match_obj.profile.name, match_obj.profile.age}")
                self._random_sleep()

                # Generate either an opener or a reply
                if item_type == 'matches':
                    message_to_send = self.messenger_service.generate_opener(
                        profile=match_obj.profile
                    ).message
                else:
                    message_to_send = self.messenger_service.generate_reply(
                        profile=match_obj.profile,
                        last_messages=match_obj.profile.last_messages,
                    ).message

                if message_to_send:
                    if item_type == 'matches':
                        match_obj.send_opener(message_to_send, mock=self.mock)
                        self.session_data.sent_openings += 1
                    else:
                        match_obj.send_reply(message_to_send, mock=self.mock)
                        self.session_data.sent_replies += 1
                else:
                    logger.info("No message to send.")

                self._random_sleep()

            except MatchReadyException:
                logger.info(
                    f"Match {match_obj.profile.name} is ready to meet."
                )
                continue
            except Exception as e:
                logger.error(f"Error processing item: {e}")
                continue
            finally:
                if match_obj is not None:
                    if item_type == 'matches':
                        self.go_to_matches()
                    else:
                        match_obj.close_profile()

    def _get_unread_messages_data(self) -> List[str]:
        """Get list of unread message data"""
        try:
            message_elements = WebDriverWait(self.browser, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "a.messageListItem")
                )
            )

            messages_data = []
            for message in message_elements:
                try:
                    message_div = message.find_element(
                        By.CSS_SELECTOR, "div.messageListItem__message"
                    )

                    has_svg = message_div.find_elements(By.TAG_NAME, "svg")
                    if has_svg:
                        # We sent the last message, skip this chat
                        continue

                    href = message.get_attribute('href')
                    message_id = href.split('/')[-1]
                    messages_data.append(message_id)
                except Exception as e:
                    logger.error(f"Error extracting message data: {e}")
                    continue

            return messages_data
        except Exception as e:
            logger.error(f"Error getting unread message elements: {e}")
            return []

    def _get_matches_data(self) -> List[str]:
        """Get list of basic match data (IDs and names)"""
        try:
            match_elements = WebDriverWait(self.browser, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "a.matchListItem")
                )
            )

            matches_data = []
            for match in match_elements:
                try:
                    href = match.get_attribute('href')
                    match_id = href.split('/')[-1]
                    matches_data.append(match_id)
                except Exception as e:
                    logger.error(f"Error extracting match data: {e}")
                    continue

            return matches_data
        except Exception as e:
            logger.error(f"Error getting match elements: {e}")
            return []

    def _handle_potential_popups(self) -> None:
        """
        Handles various popups that may appear during the session.

        This method attempts to find and dismiss several types of popups
        that can interrupt the session. The popups handled include:
        - 'See who liked you' popup
        - 'Upgrade like' popup
        - 'Add Tinder to homescreen' popup
        - Match popup
        - Superlikes popup

        If a popup is found,
        it is dismissed and an appropriate log message is recorded.
        If a popup is not found,
        the method continues to check for the next type of popup.
        In case of a stale element reference or an element not being visible,
        the browser is refreshed to attempt to resolve the issue.

        Exceptions handled:
        - NoSuchElementException: If the popup element is not found.
        - StaleElementReferenceException: If the popup element becomes stale.
        - ElementNotVisibleException: If the popup element is not visible.
        """
        # last possible id based div
        base_element = self.browser.find_element(By.XPATH, '/html/body/div[2]')

        # 'see who liked you' popup
        try:
            xpath = './/button/span[contains(text(), "Maybe Later")]'
            deny_btn = base_element.find_element(By.XPATH, xpath)
            deny_btn.click()
            logger.info("POPUP: Dismissed 'Maybe Later'")
            return
        except NoSuchElementException:
            pass

        # 'upgrade like' popup
        try:
            xpath = './/main/div/button[2]'
            base_element.find_element(By.XPATH, xpath).click()
            logger.info("POPUP: Denied upgrade to superlike")
            return
        except NoSuchElementException:
            pass

        # 'add tinder to homescreen' popup
        try:
            xpath = './/main/div/div[2]/button[2]'

            add_to_home_popup = base_element.find_element(By.XPATH, xpath)
            add_to_home_popup.click()
            logger.info("POPUP: Denied Tinder to homescreen")
            return
        except NoSuchElementException:
            pass

        # match popup
        try:
            xpath = '//button[@title="Back to Tinder"]'

            match_popup = base_element.find_element(By.XPATH, xpath)
            match_popup.click()
            self.session_data.matches += 1
        except NoSuchElementException:
            pass
        except StaleElementReferenceException:
            self.browser.refresh()

        # superlikes popup
        try:
            xpath = './/main/div/div[3]/button[2]'
            deny_btn = base_element.find_element(By.XPATH, xpath)
            deny_btn.click()
            logger.info("POPUP: Denied buying more superlikes")
        except ElementNotVisibleException:
            self.browser.refresh()
        except NoSuchElementException:
            pass
        except StaleElementReferenceException:
            self.browser.refresh()

    def _random_sleep(
        self,
        min_sleep: float = MIN_SLEEP,
        max_sleep: float = MAX_SLEEP
    ) -> float:
        """
        Sleep for a random duration between MIN_SLEEP and MAX_SLEEP
        and return the sleep time
        """
        sleep_time = random.uniform(min_sleep, max_sleep)
        time.sleep(sleep_time)
        return sleep_time

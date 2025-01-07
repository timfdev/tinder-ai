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
from bot.services.preferences import PreferencesService
from bot.services.login import LoginService
from bot_project.bot.services.messenger_api import BaseMessengerService
from bot.constants.models import LoginMethods
from bot.settings import Settings
from pathlib import Path
import random
from bot.services.match import Match
import json
from bot.services.location import LocationService
from logging import getLogger


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
        headless: bool = False,
        user_data: Path = None
    ):
        """
        Initializes a session with support for a local proxy server.
        :param settings: Configuration settings containing proxy details.
        :param headless: Run the browser in headless mode.
        :param user_data: Path to user data directory for persistent sessions.
        """
        self.session_data = {
            "duration": 0,
            "like": 0,
            "dislike": 0,
            "superlike": 0,
            "matches": 0
        }

        self.start_session = time.time()

        options = uc.ChromeOptions()
        options.binary_location = "/usr/bin/google-chrome"
        options.add_argument('--no-first-run --no-service-autorun --password-store=basic')
        options.add_argument("--lang=en")
        options.add_argument("--disable-webrtc")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/112.0.5615.138"
            " Safari/537.36"
        )
        if user_data is not None:
            options.add_argument(f"--user-data-dir=./{user_data}")
        options.add_argument("homepage=http://example.com")
        options.add_argument("--disable-notifications")

        if settings.proxy_url is not None:
            # Use local proxy server
            logger.info(f"Routing traffic through local proxy server: {settings.proxy_url}")
            options.add_argument(f"--proxy-server={settings.proxy_url}")

        if headless:
            options.headless = True

        # Allow geolocation by default
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.geolocation": 1
        })

        # Initialize the browser
        self.browser = uc.Chrome(options=options)

        self.browser.set_window_size(self.DEFAULT_WINDOW_SIZE)
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

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        """Clean up when exiting context."""
        seconds = int(time.time() - self.start_session)
        self.session_data["duration"] = seconds

        # logger.info stats
        logger.info(json.dumps(self.session_data, indent=4))

        logger.info(f"Started session: {self.started}")
        logger.info(f"Ended session: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")

        # Quit the browser
        self.browser.quit()

    def set_preferences(self):
        PreferencesService(browser=self.browser).set_preferences(settings=self.settings)

    def login(self, method: LoginMethods):
        if self._is_logged_in():
            return

        login_service = LoginService(browser=self.browser)

        if method == LoginMethods.FACEBOOK:
            if not self.settings.facebook_email or not self.settings.facebook_password:
                raise ValueError("Facebook email or password is not set. Please provide valid credentials.")

            logger.info("Logging in using Facebook")
            login_service.login_by_facebook(
                self.settings.facebook_email,
                self.settings.facebook_password
            )
        elif method == LoginMethods.GOOGLE:
            if not self.settings.google_email or not self.settings.google_password:
                raise ValueError("Google email or password is not set. Please provide valid credentials.")

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

    def _is_logged_in(self):
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
            # Wait for the app page specifically, indicating login success
            WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.url_contains("tinder.com/app")
            )
            logger.info("User is logged in.")
            return True
        except TimeoutException:
            logger.info(
                f"User is not logged in yet. Current URL:\n {self.browser.current_url}"
            )
            return False

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
            like_button = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
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
            dislike_button = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
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

    def start_swiping(self, ratio='90%'):
        """
        Start liking or disliking profiles based on the provided amount and ratio.

        :param amount: Number of profiles to process.
        :param ratio: Percentage chance to like a profile (e.g., '80%' for 80% like).
        :param sleep: Base sleep time between actions in seconds.
        """
        ratio = float(ratio.strip('%')) / 100  # Convert ratio to float (e.g., '100%' -> 1.0)

        if not self._is_logged_in():
            logger.info("Not logged in. Please log in before starting the liking process.")
            return

        matcher = Match(browser=self.browser)
        amount_liked = 0

        logger.info("\nStarting to like profiles.")
        self._handle_potential_popups()  # Initial popup handling

        while amount_liked < self.settings.swipe_limit:
            try:
                like = random.random() <= ratio

                if like:
                    if matcher.like():
                        amount_liked += 1
                        self.session_data['like'] += 1
                else:
                    matcher.dislike()
                    self.session_data['dislike'] += 1

                self._random_sleep()
                self._handle_potential_popups()
                logger.info(
                    "Processed "
                    f"{amount_liked} / {self.settings.swipe_limit} profiles."
                )
            except NoSuchElementException as e:
                logger.warning(f"Element not found during processing: {e}. Retrying...")
                self.browser.refresh()
                time.sleep(self.WEBDRIVER_WAIT_TIME)
            except TimeoutException as e:
                logger.warning(f"Timeout encountered: {e}. Retrying...")
                self.browser.refresh()
                time.sleep(self.WEBDRIVER_WAIT_TIME)
            except Exception as e:
                logger.error(f"Unexpected error occurred: {e}. Skipping this iteration.")

    def go_to_matches(self):
        """
        Navigate to the "Matches" tab.
        """
        try:
            # XPath for the "Matches" button
            matches_button_xpath = '//button[contains(text(), "Matches")]'

            # Wait for the button to be clickable
            matches_button = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, matches_button_xpath))
            )

            # Click the "Matches" button
            matches_button.click()
            logger.info("Navigated to the 'Matches' tab.")
        except TimeoutException:
            logger.error("Timeout occurred while trying to navigate to 'Matches'.")
            raise
        except Exception as e:
            logger.error(f"An error occurred while navigating to 'Matches': {e}")
            raise

    def go_to_messages(self):
        """
        Navigate to the "Messages" tab.
        """
        try:
            # XPath for the "Messages" button
            messages_button_xpath = '//button[contains(text(), "Messages")]'

            # Wait for the button to be clickable
            messages_button = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, messages_button_xpath))
            )

            # Click the "Messages" button
            messages_button.click()
            logger.info("Navigated to the 'Messages' tab.")
        except TimeoutException:
            logger.error("Timeout occurred while trying to navigate to 'Messages'.")
            raise
        except Exception as e:
            logger.error(f"An error occurred while navigating to 'Messages': {e}")
            self._handle_potential_popups()

    def handle_matches(self):
        self._random_sleep()
        self._handle_potential_popups()
        logger.info("Handling matches...")
        self.go_to_matches()
        self._random_sleep()

        # Get list of match data first
        matches_data = self._get_matches_data()
        logger.info(f"Found {len(matches_data)} matches to process")

        # Process each match using their ID
        for index, match_data in enumerate(matches_data):
            try:
                logger.info(f"Processing match {index + 1} of {len(matches_data)}")

                # Find the match element by its ID
                match_selector = f"a[href*='{match_data['id']}']"
                match_element = WebDriverWait(self.browser, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, match_selector))
                )

                # Create Match object from element
                match = Match.from_element(match_element, self.browser)

                if not match.profile.name:  # Basic validation
                    logger.warning(
                        "Could not extract match data properly for "
                        f"{match_data['name']}, skipping...")
                    continue

                logger.info(
                    "Processing match: "
                    f"{match.profile.name, match.profile.age}"
                )
                self._random_sleep()

                # Get opener message
                opener = self.messenger_service.generate_opener(
                    profile=match.profile
                )

                # Send opener message
                if opener:
                    match.send_opener(opener)
                    logger.info(f"Sent opener to {match.profile.name}")

                self._random_sleep()

            except Exception as e:
                logger.error(f"Error processing match {match_data['id']}: {e}")
                continue

    def handle_unread_messages(self):
        self._random_sleep()
        self._handle_potential_popups()
        logger.info("Handling unread messages...")
        self.go_to_messages()
        self._random_sleep()

        # Get list of unread message data
        unread_messages = self._get_unread_messages_data()

        logger.info(f"Found {len(unread_messages)} unread messages to process")

        for index, message_data in enumerate(unread_messages):
            try:
                logger.info(f"Processing message {index + 1} of {len(unread_messages)}")

                # Find the match element by its ID
                match_selector = f"a[href*='{message_data['id']}']"
                match_element = WebDriverWait(self.browser, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, match_selector))
                )

                # Create Match object from element
                match = Match.from_element(match_element, self.browser, messages=True)

                if not match.profile.name:  # Basic validation
                    logger.warning(f"Could not extract match data properly for {message_data['name']}, skipping...")
                    continue

                logger.info(f"Processing match: {match.profile}")
                self._random_sleep()

                # Get reply message
                reply = self.messenger_service.generate_reply(
                    profile=match.profile,
                    last_messages=match.profile.last_messages,
                )

                # Send reply message
                if reply:
                    match.send_reply(reply)
                    logger.info(f"Sent opener to {match.profile.name}")

                self._random_sleep()

            except Exception as e:
                logger.error(f"Error processing message {message_data['id']}: {e}")
                continue

    def _get_unread_messages_data(self):
        """Get list of unread message data"""
        try:
            message_elements = WebDriverWait(self.browser, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.messageListItem"))
            )

            messages_data = []
            for message in message_elements:
                try:
                    # Get the message content div first
                    message_div = message.find_element(By.CSS_SELECTOR, "div.messageListItem__message")

                    # Check for any SVG in message div
                    has_svg = message_div.find_elements(By.TAG_NAME, "svg")
                    if has_svg:
                        # We sent the last message, skip this chat
                        continue

                    # Get all data from message element
                    href = message.get_attribute('href')
                    message_id = href.split('/')[-1]
                    name = message.find_element(By.CSS_SELECTOR, "h3.messageListItem__name").text
                    message_content = message_div.text

                    messages_data.append({
                        'id': message_id,
                        'name': name,
                        'message': message_content,
                    })
                except Exception as e:
                    logger.error(f"Error extracting message data: {e}")
                    continue

            return messages_data
        except Exception as e:
            logger.error(f"Error getting unread message elements: {e}")
            return []

    def _get_matches_data(self):
        """Get list of basic match data (IDs and names)"""
        try:
            match_elements = WebDriverWait(self.browser, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.matchListItem"))
            )

            matches_data = []
            for match in match_elements:
                try:
                    href = match.get_attribute('href')
                    match_id = href.split('/')[-1]
                    name = match.find_element(By.CSS_SELECTOR, "div.Ell").text
                    matches_data.append({
                        'id': match_id,
                        'name': name
                    })
                except Exception as e:
                    logger.error(f"Error extracting match data: {e}")
                    continue

            return matches_data
        except Exception as e:
            logger.error(f"Error getting match elements: {e}")
            return []

    def _handle_potential_popups(self):
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
            # locate "no thanks"-button
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
            self.session_data["matches"] += 1
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
        """Sleep for a random duration between MIN_SLEEP and MAX_SLEEP and return the sleep time"""
        sleep_time = random.uniform(min_sleep, max_sleep)
        time.sleep(sleep_time)
        return sleep_time

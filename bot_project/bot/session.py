import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
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
from bot.constants.models import Xpaths, LoginMethods
from bot.settings import Settings
from pathlib import Path
import random
from bot.services.match import MatchService
import json
from bot.services.location import LocationService
from logging import getLogger


logger = getLogger(__name__)


class Session:

    WEBDRIVER_WAIT_TIME = 10

    def __init__(
        self,
        settings: Settings,
        headless: bool = False,
        user_data: Path = None,
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

        self.browser.set_window_size(1250, 750)
        self.settings = settings

        location_setter = LocationService(
            browser=self.browser,
            settings=self.settings
        )
        location_setter.configure_location()

        time.sleep(2)

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

    def login(self, method: LoginMethods = LoginMethods.FACEBOOK):
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

    def start_swiping(self, ratio='90%', sleep=1):
        """
        Start liking or disliking profiles based on the provided amount and ratio.

        :param amount: Number of profiles to process.
        :param ratio: Percentage chance to like a profile (e.g., '80%' for 80% like).
        :param sleep: Base sleep time between actions in seconds.
        """
        initial_sleep = sleep
        ratio = float(ratio.strip('%')) / 100  # Convert ratio to float (e.g., '100%' -> 1.0)

        if not self._is_logged_in():
            logger.info("Not logged in. Please log in before starting the liking process.")
            return

        matcher = MatchService(browser=self.browser)
        amount_liked = 0

        logger.info("\nStarting to like profiles.")
        self._handle_potential_popups()  # Initial popup handling

        while amount_liked < self.settings.swipe_limit:
            try:
                if not self._profile_visible():
                    raise NoSuchElementException("Profile not visible.")

                # Dynamically adjust sleep time
                sleep_time = random.uniform(0.5, 2.3) * initial_sleep
                like = random.random() <= ratio

                if like:
                    if matcher.like():
                        amount_liked += 1
                        self.session_data['like'] += 1
                else:
                    matcher.dislike()
                    self.session_data['dislike'] += 1

                time.sleep(sleep_time)
                self._handle_potential_popups()
                logger.info(
                    "Processed "
                    f"{amount_liked} / {self.settings.swipe_limit} profiles."
                )
            except NoSuchElementException as e:
                logger.info(f"Element not found during processing: {e}. Retrying...")
                self.browser.refresh()
                time.sleep(self.WEBDRIVER_WAIT_TIME)
            except TimeoutException as e:
                logger.info(f"Timeout encountered: {e}. Retrying...")
                self.browser.refresh()
                time.sleep(self.WEBDRIVER_WAIT_TIME)
            except Exception as e:
                logger.info(f"Unexpected error occurred: {e}. Skipping this iteration.")

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
            raise

    def handle_matches(self):
        self._handle_potential_popups()
        logger.info("Handling matches...")
        self.go_to_matches()
        time.sleep(2)

        # Get initial list of match elements and their IDs
        matches_data = self.get_matches_data()
        logger.info(f"Found {len(matches_data)} matches to process")

        # Process each match by finding and clicking its element
        for index, match_data in enumerate(matches_data):
            try:
                logger.info(f"Processing match {index + 1} of {len(matches_data)}")

                # Find the match element by its ID
                match_selector = f"a[href*='{match_data['id']}']"
                match_element = WebDriverWait(self.browser, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, match_selector))
                )

                details = MatchService.extract_profile_details(match_element, self.browser)
                logger.info(f"Profile details: {details}")
                time.sleep(random.uniform(1, 2))

            except Exception as e:
                logger.error(f"Error processing match {match_data['id']}: {e}")
                continue

    def get_matches_data(self):
        """Get list of matches with their IDs and names"""
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

    def _profile_visible(self):
        """
        Check if the current Tinder profile is visible.
        :return: True if the active profile card is visible and contains at least one image, False otherwise.
        """
        try:
            # XPath to locate the currently active profile card
            active_card_xpath = "//div[contains(@class, 'keen-slider__slide') and @aria-hidden='false']"
            WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, active_card_xpath))
            )

            # Locate image elements within the active profile card
            image_elements_xpath = f"{active_card_xpath}//div[contains(@style, 'background-image')]"
            image_elements = self.browser.find_elements(By.XPATH, image_elements_xpath)

            # Check if at least one image is found
            for element in image_elements:
                style = element.get_attribute('style')
                if 'url(' in style:
                    return True  # Profile is visible if at least one image URL is found

        except (StaleElementReferenceException, TimeoutException) as e:
            logger.warning(f"Handled exception while checking profile visibility: {e}")

        except Exception as e:
            logger.error(f"Unhandled exception in _profile_visible: {e}")

        return False  # Return False if no images are found or an exception occurs

    # Utilities
    def _handle_potential_popups(self):
        delay = 0.25

        # last possible id based div
        base_element = self.browser.find_element(By.XPATH, Xpaths.MODAL_MANAGER.value)

        # 'see who liked you' popup
        try:
            xpath = './/main/div/div/div[3]/button[2]'
            WebDriverWait(base_element, delay).until(
                EC.presence_of_element_located((By.XPATH, xpath)))

            deny_btn = base_element.find_element(By.XPATH, xpath)
            deny_btn.click()
            return "POPUP: Denied see who liked you"

        except NoSuchElementException:
            pass
        except TimeoutException:
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

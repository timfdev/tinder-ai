import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementNotVisibleException
)

import time
from bot.services.preferences import PreferencesHelper
from bot.services.login import LoginHelper
from bot.constants.models import Xpaths, LoginMethods
from bot.utils.addproxy import get_proxy_extension
from bot.settings import Settings
from pathlib import Path
import random
from bot.services.matcher import Matcher
import json
from bot.services.location import LocationSetter


class Session:
    def __init__(
        self, settings: Settings, headless=False,
        user_data: Path = Path("user_data"),
        use_local_proxy_server=False,
        local_proxy_url="http://localhost:3128"
    ):
        """
        Initializes a session with support for a local proxy server or direct proxy configuration.
        :param settings: Configuration settings containing proxy details.
        :param headless: Run the browser in headless mode.
        :param user_data: Path to user data directory for persistent sessions.
        :param use_local_proxy_server: If True, route traffic through a local proxy server.
        :param local_proxy_url: URL of the local proxy server (e.g., http://127.0.0.1:8080).
        """
        self.session_data = {
            "duration": 0,
            "like": 0,
            "dislike": 0,
            "superlike": 0
        }

        self.start_session = time.time()

        options = uc.ChromeOptions()
        options.binary_location = "/usr/bin/google-chrome"
        options.add_argument('--no-first-run --no-service-autorun --password-store=basic')
        options.add_argument("--lang=en-MY")
        options.add_argument("--disable-webrtc")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/112.0.5615.138"
            " Safari/537.36"
        )
        options.add_argument(f"--user-data-dir=./{user_data}")
        options.add_argument("homepage=http://example.com")
        options.add_argument("--disable-notifications")

        if use_local_proxy_server:
            # Use local proxy server
            print(f"Routing traffic through local proxy server: {local_proxy_url}")
            options.add_argument(f"--proxy-server={local_proxy_url}")

        elif settings.proxy:
            # Configure upstream proxy in extension
            print("Configuring upstream proxy in extension")
            proxy_folder = get_proxy_extension(settings.proxy)
            options.add_argument(f"--load-extension={proxy_folder}")

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

        location_setter = LocationSetter(
            browser=self.browser,
            settings=self.settings,
            local_proxy_url=local_proxy_url
        )
        location_setter.configure_location()

        self.started = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"Started session: {self.started}\n\n")

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        """Clean up when exiting context."""
        seconds = int(time.time() - self.start_session)
        self.session_data["duration"] = seconds

        # Print stats
        json.dumps(self.session_data, indent=4)

        print(f"Started session: {self.started}")
        print(f"Ended session: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")

        # Quit the browser
        self.browser.quit()

    def set_preferences(self):
        PreferencesHelper(browser=self.browser).set_preferences(settings=self.settings)

    def login(self, method: LoginMethods = LoginMethods.FACEBOOK):
        if not self._is_logged_in():
            helper = LoginHelper(browser=self.browser)
            if method == LoginMethods.FACEBOOK:
                print("Logging in using Facebook")
                helper.login_by_facebook(
                    self.settings.facebook_email,
                    self.settings.facebook_password
                )
            elif method == LoginMethods.GOOGLE:
                print("Logging in using Google")
                helper.login_by_google(
                    self.settings.google_email,
                    self.settings.google_password
                )
            else:
                raise Exception("Unsupported login method")

        if not self._is_logged_in():
            print('Manual interference is required.')
            input('Press ENTER to continue')
        elif self._is_logged_in():
            print("User is logged in.")

    def _is_logged_in(self):
        if "tinder.com" not in self.browser.current_url:
            self.browser.get("https://tinder.com/?lang=en")
            try:
                WebDriverWait(self.browser, 5).until(
                    EC.url_contains("tinder.com")
                )
            except TimeoutException:
                print("Timeout while waiting for Tinder to load.")
                return False

        try:
            # Wait for the app page specifically, indicating login success
            WebDriverWait(self.browser, 5).until(
                EC.url_contains("tinder.com/app")
            )
            print("User is logged in.")
            return True
        except TimeoutException:
            print("User is not logged in yet. Current URL:", self.browser.current_url)
            return False

    def start_swiping(self, amount=5, ratio='90%', sleep=1):
        """
        Start liking or disliking profiles based on the provided amount and ratio.

        :param amount: Number of profiles to process.
        :param ratio: Percentage chance to like a profile (e.g., '80%' for 80% like).
        :param sleep: Base sleep time between actions in seconds.
        """
        initial_sleep = sleep
        ratio = float(ratio.strip('%')) / 100  # Convert ratio to float (e.g., '100%' -> 1.0)

        if not self._is_logged_in():
            print("Not logged in. Please log in before starting the liking process.")
            return

        matcher = Matcher(browser=self.browser)
        amount_liked = 0

        print("\nStarting to like profiles.")
        self._handle_potential_popups()  # Initial popup handling

        while amount_liked < amount:
            try:
                # Dynamically adjust sleep time
                sleep_time = random.uniform(0.5, 2.3) * initial_sleep
                like = random.random() <= ratio

                if like:
                    if matcher.like():
                        amount_liked += 1
                        self.session_data['like'] += 1
                        print(f"Profile liked: {amount_liked}/{amount}. Sleeping for {sleep_time:.2f} seconds.")
                else:
                    matcher.dislike()
                    self.session_data['dislike'] += 1
                    print(f"Profile disliked. Sleeping for {sleep_time:.2f} seconds.")

                time.sleep(sleep_time)  # Wait before the next action
                self._handle_potential_popups()  # Check for popups after each action

            except NoSuchElementException as e:
                print(f"Element not found during processing: {e}. Retrying...")
            except TimeoutException as e:
                print(f"Timeout encountered: {e}. Retrying...")
            except Exception as e:
                print(f"Unexpected error occurred: {e}. Skipping this iteration.")

        print(f"\nFinished liking profiles. Total liked: {amount_liked}, Total disliked: {self.session_data['dislike']}.")


    # def get_chat_ids(self, new=True, messaged=True):
    #     if self._is_logged_in():
    #         helper = MatchHelper(browser=self.browser)
    #         self._handle_potential_popups()
    #         return helper.get_chat_ids(new, messaged)

    # def get_new_matches(self, amount=100000, quickload=True):
    #     if self._is_logged_in():
    #         helper = MatchHelper(browser=self.browser)
    #         self._handle_potential_popups()
    #         return helper.get_new_matches(amount, quickload)

    # def get_messaged_matches(self, amount=100000, quickload=True):
    #     if self._is_logged_in():
    #         helper = MatchHelper(browser=self.browser)
    #         self._handle_potential_popups()
    #         return helper.get_messaged_matches(amount, quickload)

    # def send_message(self, chatid, message):
    #     if self._is_logged_in():
    #         helper = MatchHelper(browser=self.browser)
    #         self._handle_potential_popups()
    #         helper.send_message(chatid, message)

    # def send_gif(self, chatid, gifname):
    #     if self._is_logged_in():
    #         helper = MatchHelper(browser=self.browser)
    #         self._handle_potential_popups()
    #         helper.send_gif(chatid, gifname)

    # def send_song(self, chatid, songname):
    #     if self._is_logged_in():
    #         helper = MatchHelper(browser=self.browser)
    #         self._handle_potential_popups()
    #         helper.send_song(chatid, songname)

    # def send_socials(self, chatid, media):
    #     if self._is_logged_in():
    #         helper = MatchHelper(browser=self.browser)
    #         self._handle_potential_popups()
    #         helper.send_socials(chatid, media)

    # def unmatch(self, chatid):
    #     if self._is_logged_in():
    #         helper = MatchHelper(browser=self.browser)
    #         self._handle_potential_popups()
    #         helper.unmatch(chatid)

    # Utilities
    def _handle_potential_popups(self):
        delay = 0.25

        # last possible id based div
        base_element = self.browser.find_element(By.XPATH, Xpaths.MODAL_MANAGER.value)

        # accept cookies
        try:
            xpath = './/main/div[2]/div/div/div[1]/div[1]/button'
            accept = base_element.find_element(By.XPATH, xpath)
            accept.click()
            self._handle_potential_popups()
            return "POPUP: Accepted cookies"
        except NoSuchElementException:
            pass

        # turn off notifcation popup
        try:
            xpath = './/main/div[1]/div/div/div[3]/button[2]'
            not_now = base_element.find_element(By.XPATH, xpath)
            not_now.click()
            self._handle_potential_popups()
            return "POPUP: Turned off notifications"
        except NoSuchElementException:
            pass

        # try to deny see who liked you
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

        # Try to dismiss a potential 'upgrade like' popup
        try:
            # locate "no thanks"-button
            xpath = './/main/div/button[2]'
            base_element.find_element(By.XPATH, xpath).click()
            return "POPUP: Denied upgrade to superlike"
        except NoSuchElementException:
            pass

        # try to deny 'add tinder to homescreen'
        try:
            xpath = './/main/div/div[2]/button[2]'

            add_to_home_popup = base_element.find_element(By.XPATH, xpath)
            add_to_home_popup.click()
            return "POPUP: Denied Tinder to homescreen"

        except NoSuchElementException:
            pass

        # deny buying more superlikes
        try:
            xpath = './/main/div/div[3]/button[2]'
            deny = base_element.find_element(By.XPATH, xpath)
            deny.click()
            return "POPUP: Denied buying more superlikes"
        except NoSuchElementException:
            pass

        # try to dismiss match
        matched = False
        try:
            xpath = '//button[@title="Back to Tinder"]'

            match_popup = base_element.find_element(By.XPATH, xpath)
            match_popup.click()
            matched = True

        except NoSuchElementException:
            pass
        except:
            matched = True
            self.browser.refresh()

        if matched and self.may_send_email:
            try:
                EmailHelper.send_mail_match_found(self.email)
            except:
                print("Some error occurred when trying to send mail.")
                print("Consider opening an Issue on Github.")
                pass
            return "POPUP: Dismissed NEW MATCH"

        # try to say 'no thanks' to buy more (super)likes
        try:
            xpath = './/main/div/div[3]/button[2]'
            deny_btn = base_element.find_element(By.XPATH, xpath)
            deny_btn.click()
            return "POPUP: Denied buying more superlikes"

        except ElementNotVisibleException:
            # element is not clickable, probably cuz it's out of view but still there
            self.browser.refresh()
        except NoSuchElementException:
            pass
        except:
            # TBD add stale element exception for now just refresh page
            self.browser.refresh()
            pass

        # Deny confirmation of email
        try:
            xpath = './/main/div/div[1]/div[2]/button[2]'
            remindmelater = base_element.find_element(By.XPATH, xpath)
            remindmelater.click()

            time.sleep(3)
            # handle other potential popups
            self._handle_potential_popups()
            return "POPUP: Deny confirmation of email"
        except:
            pass

        # Deny add location popup
        try:
            xpath = ".//*[contains(text(), 'No Thanks')]"
            nothanks = base_element.find_element(By.XPATH, xpath)
            nothanks.click()
            time.sleep(3)
            # handle other potential popups
            self._handle_potential_popups()
            return "POPUP: Deny confirmation of email"
        except:
            pass

        return None
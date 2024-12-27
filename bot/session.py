# from webdriver_manager.chrome import ChromeDriverManager
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
from bot.helpers.preferences import PreferencesHelper
from bot.helpers.login import LoginHelper
from bot.constants.models import Xpaths
from bot.utils.addproxy import get_proxy_extension
from bot.settings import Settings
from pathlib import Path
import random
from bot.helpers.matcher import Matcher


class Session:
    def __init__(
        self, settings: Settings, headless=False,
        user_data: Path = Path("user_data"),
        use_local_proxy_server=False,
        local_proxy_url="http://127.0.0.1:3128"
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


        if use_local_proxy_server:
            # Use local proxy server
            print(f"Routing traffic through local proxy server: {local_proxy_url}")
            options.add_argument(f"--proxy-server={local_proxy_url}")

        elif settings.proxy:
            # Configure upstream proxy directly
            print("Configuring upstream proxy in extension")
            proxy_folder = get_proxy_extension(settings.proxy)
            options.add_argument(f"--load-extension={proxy_folder}")
            proxy_url = f"http://{settings.proxy.user}:{settings.proxy.pwd}@{settings.proxy.host}:{settings.proxy.port}"
            options.add_argument(f'--proxy-server={proxy_url}')

        if headless:
            options.headless = True

        # Initialize the browser
        self.browser = uc.Chrome(options=options)

        self.browser.set_window_size(1250, 750)
        self.settings = settings

        self.started = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"Started session: {self.started}\n\n")

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        """Clean up when exiting context."""
        seconds = int(time.time() - self.start_session)
        self.session_data["duration"] = seconds

        # Print stats
        lines = [
            f"{key}: {val}" for key, val in self.session_data.items()
        ]
        box = self._get_msg_box(lines=lines, title="ai-tinder")
        print(box)

        print(f"Started session: {self.started}")
        print(f"Ended session: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")

        # Quit the browser
        self.browser.quit()

    def set_preferences(self):
        PreferencesHelper(browser=self.browser, settings=self.settings).set_preferences()

    def login_using_facebook(self):
        if not self._is_logged_in():
            print("Logging in using Facebook")
            helper = LoginHelper(browser=self.browser)
            helper.login_by_facebook(
                self.settings.facebook_email,
                self.settings.facebook_password
            )
        if not self._is_logged_in():
            print('Manual interference is required.')
            input('press ENTER to continue')

        elif self._is_logged_in():
            print("User is logged in.")

    def like(self, amount=5, ratio='100%', sleep=1, randomize_sleep=True):

        initial_sleep = sleep
        ratio = float(ratio.split('%')[0]) / 100

        if self._is_logged_in():
            matcher = Matcher(browser=self.browser)
            amount_liked = 0
            # handle one time up front, from then on check after every action instead of before
            self._handle_potential_popups()

            print("\nLiking profiles started.")
            while amount_liked < amount:
                # randomize sleep
                if randomize_sleep:
                    sleep = random.uniform(0.5, 2.3) * initial_sleep
                if random.random() <= ratio:
                    if matcher.like():
                        amount_liked += 1
                        # update for stats after session ended
                        self.session_data['like'] += 1
                        print(f"{amount_liked}/{amount} liked, sleep: {sleep}")
                else:
                    matcher.dislike()
                    # update for stats after session ended
                    self.session_data['dislike'] += 1

                #self._handle_potential_popups()
                time.sleep(sleep)

            self._print_liked_stats()

    # def dislike(self, amount=1):
    #     if self._is_logged_in():
    #         helper = GeomatchHelper(browser=self.browser)
    #         for _ in range(amount):
    #             self._handle_potential_popups()
    #             helper.dislike()

    #             # update for stats after session ended
    #             self.session_data['dislike'] += 1
    #             #time.sleep(1)
    #         self._print_liked_stats()

    # def superlike(self, amount=1):
    #     if self._is_logged_in():
    #         helper = GeomatchHelper(browser=self.browser)
    #         for _ in range(amount):
    #             self._handle_potential_popups()
    #             helper.superlike()
    #             # update for stats after session ended
    #             self.session_data['superlike'] += 1
    #             time.sleep(1)
    #         self._print_liked_stats()

    # def get_geomatch(self, quickload=True):
    #     if self._is_logged_in():
    #         helper = GeomatchHelper(browser=self.browser)
    #         self._handle_potential_popups()

    #         name = None
    #         attempts = 0
    #         max_attempts = 3
    #         while not name and attempts < max_attempts:
    #             attempts += 1
    #             name = helper.get_name()
    #             self._handle_potential_popups() # Popup handling on first geomatch
    #             time.sleep(1)

    #         age = helper.get_age()

    #         bio, passions, lifestyle, basics, anthem, looking_for = helper.get_bio_and_passions()
    #         image_urls = helper.get_image_urls(quickload)
    #         instagram = helper.get_insta(bio)
    #         rowdata = helper.get_row_data()
    #         work = rowdata.get('work')
    #         study = rowdata.get('study')
    #         home = rowdata.get('home')
    #         distance = rowdata.get('distance')
    #         gender = rowdata.get('gender')

    #         return Geomatch(name=name, age=age, work=work, gender=gender, study=study, home=home, distance=distance,
    #                         bio=bio, passions=passions, lifestyle=lifestyle, basics=basics, anthem=anthem, looking_for=looking_for, image_urls=image_urls, instagram=instagram)

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

    def _is_logged_in(self):
        time.sleep(3)
        # make sure tinder website is loaded for the first time
        if not "tinder" in self.browser.current_url:
            # enforce english language
            self.browser.get("https://tinder.com/?lang=en")
            time.sleep(100.5)

        if "tinder.com/app/" in self.browser.current_url:
            return True
        else:
            print("User is not logged in yet.\n")
            return False

    def _get_msg_box(self, lines, indent=1, width=None, title=None):
        """Print message-box with optional title."""
        space = " " * indent
        if not width:
            width = max(map(len, lines))
        box = f'/{"=" * (width + indent * 2)}\\\n'  # upper_border
        if title:
            box += f'|{space}{title:<{width}}{space}|\n'  # title
            box += f'|{space}{"-" * len(title):<{width}}{space}|\n'  # underscore
        box += ''.join([f'|{space}{line:<{width}}{space}|\n' for line in lines])
        box += f'\\{"=" * (width + indent * 2)}/'  # lower_border
        return box

    def _print_liked_stats(self):
        likes = self.session_data['like']
        dislikes = self.session_data['dislike']
        superlikes = self.session_data['superlike']

        if superlikes > 0:
            print(f"You've superliked {self.session_data['superlike']} profiles during this session.")
        if likes > 0:
            print(f"You've liked {self.session_data['like']} profiles during this session.")
        if dislikes > 0:
            print(f"You've disliked {self.session_data['dislike']} profiles during this session.")


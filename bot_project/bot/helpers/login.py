from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time


class LoginHelper:
    delay = 5

    def __init__(self, browser):
        self.browser = browser
        self._accept_cookies()

    def _click_login_button(self):
        try:
            xpath = "//a[contains(., 'Log in')]"

            wait = WebDriverWait(self.browser, self.delay)
            button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            # Ensure the button is displayed before clicking
            if button.is_displayed():
                button.click()
                print("Button clicked successfully!")
            else:
                print("Button is not displayed.")
            button.click()
            time.sleep(3)

        except TimeoutException:
            raise

        except ElementClickInterceptedException:
            pass

    def login_by_google(self, email, password):
        self._click_login_button()

        # wait for google button to appear
        xpath = '//*[@aria-label="Log in with Google"]'
        try:
            WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located(
                (By.XPATH, xpath)))

            self.browser.find_element(By.XPATH, xpath).click()

        except TimeoutException:
            raise
        except StaleElementReferenceException:
            # page was still loading when attempting to click facebook login
            time.sleep(4)
            self.browser.find_element(By.XPATH, xpath).click()

        if not self._change_focus_to_pop_up():
            print("FAILED TO CHANGE FOCUS TO POPUP")
            print("Let's try again...")
            return self.login_by_google(email, password)

        try:
            xpath = "//input[@type='email']"
            WebDriverWait(self.browser, self.delay).until(
                EC.presence_of_element_located((By.XPATH, xpath)))

            emailfield = self.browser.find_element(By.XPATH, xpath)
            emailfield.send_keys(email)
            emailfield.send_keys(Keys.ENTER)
            # sleeping 3 seconds for passwordfield to come through
            time.sleep(3)
        except TimeoutException:
            raise

        try:
            xpath = "//input[@type='password']"
            WebDriverWait(self.browser, self.delay).until(
                EC.presence_of_element_located((By.XPATH, xpath)))

            pwdfield = self.browser.find_element(By.XPATH, xpath)
            pwdfield.send_keys(password)
            pwdfield.send_keys(Keys.ENTER)

        except TimeoutException:
            raise

        self._change_focus_to_main_window()
        self._handle_popups()

    def login_by_facebook(self, email, password):

        print("Logging in with Facebook...")
        self._click_login_button()

        # Wait for Facebook login button
        try:
            xpath = '//*[@aria-label="Log in with Facebook"]'
            WebDriverWait(self.browser, self.delay).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            self.browser.find_element(By.XPATH, xpath).click()
            print("Clicked Facebook login button.")
        except TimeoutException:
            print("Timeout while waiting for Facebook login button.")
            raise
            return

        # Switch to popup
        if not self._change_focus_to_pop_up():
            print("Failed to switch focus to Facebook popup.")
            return self.login_by_facebook(email, password)

        # Handle "Continue as" or fallback to email/password
        try:
            # Check for "Continue as" button dynamically
            xpath_continue = '//div[starts-with(@aria-label, "Continue as")]'
            WebDriverWait(self.browser, self.delay).until(
                EC.presence_of_element_located((By.XPATH, xpath_continue))
            )
            self.browser.find_element(By.XPATH, xpath_continue).click()
            print("Clicked 'Continue as' button.")
        except TimeoutException:
            print("'Continue as' button not found. Falling back to manual login...")

            # Fallback to entering email and password
            try:
                xpath_email = '//*[@id="email"]'
                xpath_password = '//*[@id="pass"]'
                xpath_button = '//*[@id="loginbutton"]'

                # Wait for email field and enter credentials
                emailfield = WebDriverWait(self.browser, self.delay).until(
                    EC.presence_of_element_located((By.XPATH, xpath_email))
                )
                emailfield.send_keys(email)

                pwdfield = WebDriverWait(self.browser, self.delay).until(
                    EC.presence_of_element_located((By.XPATH, xpath_password))
                )
                pwdfield.send_keys(password)

                loginbutton = self.browser.find_element(By.XPATH, xpath_button)
                loginbutton.click()
                print("Logged in via Facebook.")
            except TimeoutException:
                print("Timeout occurred during manual Facebook login.")
                raise

        # Switch back to main window
        self._change_focus_to_main_window()
        self._handle_popups()

    def _handle_prefix(self, country):
        self._accept_cookies()

        xpath = '//div[@aria-describedby="phoneErrorMessage"]/div/div'
        WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located(
            (By.XPATH, xpath)))
        btn = self.browser.find_element(By.XPATH, xpath)
        btn.click()

        els = self.browser.find_elements(By.XPATH, '//div')
        for el in els:
            try:
                span = el.find_element(By.XPATH, './/span')
                if span.text.lower() == country.lower():
                    print("clicked")
                    el.click()
                    break
                else:
                    print(span.text)
            except:
                continue

    def _handle_popups(self):
        print("Handling popups...")
        time.sleep(2)
        self._accept_cookies()
        self._accept_location_notification()
        self._deny_overlayed_notifications()
        time.sleep(5)

    def _accept_location_notification(self):
        try:
            xpath = '//*[@data-testid="allow"]'
            WebDriverWait(self.browser, self.delay).until(
                EC.presence_of_element_located((By.XPATH, xpath)))

            locationBtn = self.browser.find_element(By.XPATH, xpath)
            locationBtn.click()
            print("ACCEPTED LOCATION.")
        except TimeoutException:
            print(
                "ACCEPTING LOCATION: Loading took too much time! Element probably not presented, so we continue.")
        except:
            pass

    def _deny_overlayed_notifications(self):
        try:
            xpath = '//*[@data-testid="decline"]'
            WebDriverWait(self.browser, self.delay).until(
                EC.presence_of_element_located((By.XPATH, xpath)))

            self.browser.find_element(By.XPATH, xpath).click()
            print("DENIED NOTIFICATIONS.")
        except TimeoutException:
            print(
                "DENYING NOTIFICATIONS: Loading took too much time! Element probably not presented, so we continue.")
        except:
            pass

    def _accept_cookies(self):
        print("Accepting cookies...")
        try:
            xpath = '//*[@type="button"]'
            WebDriverWait(self.browser, self.delay).until(
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
                        print("COOKIES ACCEPTED.")
                        time.sleep(1.5)
                        break
                except NoSuchElementException:
                    pass

        except TimeoutException:
            print(
                "ACCEPTING COOKIES: Loading took too much time! Element probably not present, so we continue."
            )
        except Exception as e:
            print("Error while accepting cookies:", e)

    def _change_focus_to_pop_up(self):
        max_tries = 50
        current_tries = 0

        main_window = None
        while not main_window and current_tries < max_tries:
            current_tries += 1
            main_window = self.browser.current_window_handle

        current_tries = 0
        popup_window = None
        while not popup_window:
            current_tries += 1
            time.sleep(0.30)
            if current_tries >= max_tries:
                print("tries exceeded")
                return False

            for handle in self.browser.window_handles:
                if handle != main_window:
                    popup_window = handle
                    break

        self.browser.switch_to.window(popup_window)
        return True

    def _change_focus_to_main_window(self):
        main_window = None
        if len(self.browser.window_handles) == 1:
            main_window = self.browser.current_window_handle
        else:
            popup_window = self.browser.current_window_handle
            while not main_window:
                for handle in self.browser.window_handles:
                    if handle != popup_window:
                        main_window = handle
                        break

        self.browser.switch_to.window(main_window)

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException
)
from selenium.webdriver.common.action_chains import ActionChains
from bot.src.constants.models import Sexuality
from bot.src.settings import Settings
import time
import random
from logging import getLogger


logger = getLogger(__name__)


class PreferencesService:
    WEBDRIVER_WAIT_TIME = 10

    def __init__(self, browser):
        self.browser = browser
        try:
            logger.info('Open profile')
            xpath = '//*[@href="/app/profile"]'
            profile_button = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, xpath)))
            profile_button.click()
            logger.info('found profile page')
        except TimeoutException:
            logger.info("Timeout while opening profile")
        except Exception as e:
            logger.info(f"Error opening profile: {e}")

    def set_preferences(self, settings: Settings):
        self.set_distance_range(settings.distance_range)
        time.sleep(random.randint(0, 2))
        self.set_age_range(settings.age_range_min, settings.age_range_max)
        time.sleep(random.randint(0, 2))
        self.set_sexuality(settings.gender_preference)
        time.sleep(random.randint(0, 2))
        self.set_global(settings.set_global)
        time.sleep(random.randint(1, 3))
        self.navigate_to_main_screen()
        time.sleep(random.randint(1, 3))

    def set_custom_location(self, latitude, longitude, accuracy="100%"):
        """Sets a custom geolocation for the browser."""
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "accuracy": int(accuracy.split('%')[0])
            }
            self.browser.execute_cdp_cmd("Page.setGeolocationOverride", params)
        except Exception as e:
            logger.info(f"Error setting custom location: {e}")

    def set_distance_range(self, km):
        """Sets the distance range using slider manipulation."""
        try:
            # Correct out-of-bounds values
            final_percentage = min(max((km / 161) * 100, 0), 100)

            slider_handle_xpath = '//div[@role="slider" and @aria-label="Maximum distance in kilometers"]'
            slider_track_xpath = '//*[@data-testid="slider-rail"]'

            # Locate the slider handle and track
            slider_handle = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, slider_handle_xpath))
            )
            slider_track = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, slider_track_xpath))
            )

            # Extract the current percentage from the 'style' attribute
            current_percentage = float(slider_handle.get_attribute('style').split('left: ')[1].replace('%;', '').strip())

            # Dynamically retrieve the slider's total width
            slider_track_width_px = slider_track.size['width']

            # Calculate movement
            pixel_distance_to_move = ((final_percentage - current_percentage) / 100) * slider_track_width_px

            # Adjust the slider in small steps
            action = ActionChains(self.browser).click_and_hold(slider_handle)
            steps = max(1, int(abs(pixel_distance_to_move) / 5))
            step_distance = pixel_distance_to_move / steps

            for _ in range(steps):
                action.move_by_offset(step_distance, 0)

            action.release().perform()

            # Verify the slider's final position
            time.sleep(0.5)
            updated_percentage = float(slider_handle.get_attribute('style').split('left: ')[1].replace('%;', '').strip())
            logger.info(f"Ended slider with distance from {updated_percentage * 1.61:.1f} km to {final_percentage * 1.61:.1f} km\n\n")

        except Exception as e:
            logger.info(f"Error setting distance range: {e}")

    def set_age_range(self, min_age, max_age):
        """Sets the age range using slider manipulation."""
        try:
            min_slider = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, '//*[@data-testid="min-age-handle"]'))
            )
            max_slider = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, '//*[@data-testid="max-age-handle"]'))
            )

            def adjust_slider(slider, target_age, slider_type):
                current_age = int(slider.get_attribute('aria-valuenow'))
                logger.info(f"\nAdjusting {slider_type} from {current_age} to {target_age} years")

                if current_age == target_age:
                    return current_age

                # Start holding the slider
                action = ActionChains(self.browser)
                action.click_and_hold(slider)
                action.perform()
                time.sleep(0.1)

                while True:
                    current_age = int(slider.get_attribute('aria-valuenow'))
                    if current_age == target_age:
                        break

                    # Calculate movement based on distance to target
                    age_diff = target_age - current_age
                    # Movement grows with distance but stays proportional
                    movement = abs(age_diff) * 0.5  # This will make it move faster when far, slower when close
                    pixels = movement if age_diff > 0 else -movement

                    action = ActionChains(self.browser)
                    action.move_by_offset(pixels, 0)
                    action.perform()
                    time.sleep(0.1)

                    # Prevent infinite loop if we can't hit exact target
                    if abs(age_diff) <= 1:
                        break

                # Release the slider
                action = ActionChains(self.browser)
                action.release()
                action.perform()

                final_age = int(slider.get_attribute('aria-valuenow'))
                logger.info(f"Finished at age: {final_age}")
                return final_age

            # Adjust both sliders
            min_age = max(18, min(min_age, 100))
            max_age = min(100, max(max_age, min_age))

            final_min = adjust_slider(min_slider, min_age, "Minimum")
            time.sleep(0.3)
            final_max = adjust_slider(max_slider, max_age, "Maximum")

            logger.info(f"Final age range: {final_min}-{final_max} years")

        except Exception as e:
            logger.info(f"Error setting age range: {e}")

    def set_sexuality(self, type: Sexuality):
        """
        Sets the sexuality preference with enhanced error handling.
        """
        try:
            # Locate the "Looking for" button
            settings_button_xpath = "//button[@aria-label='Looking for' and not(@data-id) and not(@data-route)]"
            settings_button = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, settings_button_xpath))
            )

            # Click the settings button
            actions = ActionChains(self.browser)
            actions.move_to_element(settings_button).click().perform()
            time.sleep(0.3)

            # Wait for the checkbox list to appear
            WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, "//ul[contains(@class, 'List')]"))
            )

            # Uncheck all selected checkboxes
            checkboxes = self.browser.find_elements(By.XPATH, "//input[@type='checkbox']")
            for checkbox in checkboxes:
                try:
                    if checkbox.is_selected():
                        label = checkbox.find_element(
                            By.XPATH, f"//label[@for='{checkbox.get_attribute('id')}']"
                        )
                        actions.move_to_element(label).click().perform()
                except StaleElementReferenceException:
                    logger.info("Checkbox element became stale; attempting to refresh and continue.")
                    # Refresh the list of checkboxes
                    checkboxes = self.browser.find_elements(By.XPATH, "//input[@type='checkbox']")

            # Locate and select the given option
            option_xpath = f"//label[contains(., '{type.value}')]"
            option = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, option_xpath))
            )
            actions.move_to_element(option).click().perform()

        except StaleElementReferenceException:
            logger.info("Element became stale during interaction. Retrying...")
            self.set_sexuality(type)  # Retry the operation
        except TimeoutException:
            logger.info("Timed out waiting for elements. Please check the page state.")
        except Exception as e:
            logger.info(f"An unexpected error occurred: {e}")
        finally:
            # Close the settings menu
            self.navigate_to_main_settings()

    def set_global(self, enable_global):
        """
        Toggle global mode to ensure it's explicitly set.
        :param enable_global: Boolean indicating whether to enable or disable global mode.
        """
        try:
            # Locate the toggle input element for the Global option
            xpath_global_toggle = '//input[@name="global" and @type="checkbox"]'
            global_toggle = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, xpath_global_toggle))
            )

            # Check the current state of the toggle
            is_activated = global_toggle.get_attribute("aria-checked") == "true"

            # Toggle only if necessary
            if enable_global != is_activated:
                global_toggle.click()
                logger.info(f"Global mode {'enabled' if enable_global else 'disabled'} successfully.")
            else:
                # Even if the state matches, we toggle it off and back on
                global_toggle.click()  # Turn it off
                WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
                    lambda _: global_toggle.get_attribute("aria-checked") == str(not enable_global).lower()
                )
                time.sleep(0.5)
                global_toggle.click()  # Turn it back on
                logger.info(f"Global mode {'enabled' if enable_global else 'disabled'}.")

        except Exception as e:
            logger.error(f"Error occurred in set_global: {e}")

    def navigate_to_main_settings(self):
        actions = ActionChains(self.browser)
        # Navigate back to the main settings page
        profile_button_xpath = "//a[@title='My Profile' and contains(@href, '/app/profile')]"
        profile_button = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
            EC.element_to_be_clickable((By.XPATH, profile_button_xpath))
        )
        actions.move_to_element(profile_button).click().perform()
        logger.info("Navigated back to the main settings page.")

    def navigate_to_main_screen(self):
        """
        Navigate back to the main screen for liking profiles.
        """
        actions = ActionChains(self.browser)
        back_button_xpath = "//a[@title='Back' and contains(@href, '/app/recs')]"
        back_button = WebDriverWait(self.browser, self.WEBDRIVER_WAIT_TIME).until(
            EC.element_to_be_clickable((By.XPATH, back_button_xpath))
        )
        actions.move_to_element(back_button).click().perform()
        logger.info("Navigated back to the main screen for liking profiles.")
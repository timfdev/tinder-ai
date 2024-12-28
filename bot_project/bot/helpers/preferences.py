from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import random
from bot.constants.models import Sexuality
import time

class PreferencesHelper:

    delay = 8

    HOME_URL = "https://www.tinder.com/app/profile"

    def __init__(self, browser):
        self.browser = browser

        # open profile
        try:
            print('Open profile')
            xpath = '//*[@href="/app/profile"]'
            WebDriverWait(self.browser, self.delay).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            self.browser.find_element(By.XPATH, xpath).click()
            print('found profile page')
        except:
            pass

    def set_preferences(self):
        self.set_distance_range(15)
        self.set_age_range(18, 55)
        self.set_sexualitiy
        self.set_global(True)

    # Setting a custom location
    def set_custom_location(self, latitude, longitude, accuracy="100%"):

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": int(accuracy.split('%')[0])
        }

        self.browser.execute_cdp_cmd("Page.setGeolocationOverride", params)

    def set_distance_range(self, km):
        # correct out of bounds values
        if km > 160:
            final_percentage = 100
        elif km < 2:
            final_percentage = 0
        else:
            final_percentage = (km / 160) * 100

        possible_xpaths = ['//*[@aria-label="Maximum distance in kilometres"]',
                           '//*[@aria-label="Maximum distance in kilometers"]',
                           '//*[@aria-label="Maximum distance in miles"]']

        for xpath in possible_xpaths:
            try:
                WebDriverWait(self.browser, self.delay).until(
                    EC.presence_of_element_located((By.XPATH, xpath)))
                link = self.browser.find_element(By.XPATH, xpath)
                break
            except TimeoutException:
                continue

        print("\nSlider of distance will be adjusted...")
        current_percentage = float(link.get_attribute('style').split(' ')[1].split('%')[0])
        print("from {}% = {}km".format(current_percentage, current_percentage*1.6))
        print("to {}% = {}km".format(final_percentage, final_percentage*1.6))
        print("with a fault margin of 1%\n")

        slider_track_xpath = "//*[@data-testid='slider-rail']"
        slider_handle_xpath = '//*[@aria-label="Maximum distance in kilometers"]'

        slider_track = WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.XPATH, slider_track_xpath)))
        slider_handle = WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.XPATH, slider_handle_xpath)))

        # Dynamically retrieve the slider's total width
        slider_track_width_px = slider_track.size['width']

        # Calculate the pixel distance needed to move based on the current and target percentages
        pixel_distance_to_move = ((final_percentage - current_percentage) / 100) * slider_track_width_px

        # Use ActionChains to drag the slider handle by the calculated pixel distance
        action = ActionChains(self.browser).click_and_hold(slider_handle)
        steps = 10  # You can adjust the number of steps based on your needs

        # Calculate the distance for each small step
        step_distance = pixel_distance_to_move / steps

        # Introduce randomness in each step to simulate more natural movement
        for _ in range(steps):
            # Add a small random value to each step's distance to simulate slight variance in human movement
            # Adjust the range of randomness (-0.5 to 0.5 here) as needed
            random_step_distance = step_distance + random.uniform(-0.5, 0.5)

            # Also introduce a slight vertical randomness to simulate imperfect straight-line movement
            # Be cautious with vertical movement to avoid unwanted interactions
            action.move_by_offset(random_step_distance, random.uniform(-1, 1))

        # Release the slider handle after completing the movement
        action.release()

        # Perform the entire sequence of actions
        action.perform()

        print("Ended slider with {}% = {}km\n\n".format(current_percentage, current_percentage*1.6))
        time.sleep(5)

    def set_age_range(self, min, max):
        # locate elements
        xpath = '//*[@aria-label="Minimum age"]'
        WebDriverWait(self.browser, self.delay).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        btn_minage = self.browser.find_element(By.XPATH, xpath)

        xpath = '//*[@aria-label="Maximum age"]'
        WebDriverWait(self.browser, self.delay).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        btn_maxage = self.browser.find_element(By.XPATH, xpath)

        min_age_tinder = int(btn_maxage.get_attribute('aria-valuemin'))
        max_age_tinder = int(btn_maxage.get_attribute('aria-valuemax'))

        # correct out of bounds values
        if min < min_age_tinder:
            min = min_age_tinder

        if max > max_age_tinder:
            max = max_age_tinder

        while max-min < 5:
            max += 1
            min -= 1

            if min < min_age_tinder:
                min = min_age_tinder
            if max > max_age_tinder:
                max = max_age_tinder

        range_ages_tinder = max_age_tinder - min_age_tinder
        percentage_per_year = 100 / range_ages_tinder

        to_percentage_min = (min - min_age_tinder) * percentage_per_year
        to_percentage_max = (max - min_age_tinder) * percentage_per_year

        current_percentage_min = float(btn_minage.get_attribute('style').split(' ')[1].split('%')[0])
        current_percentage_max = float(btn_maxage.get_attribute('style').split(' ')[1].split('%')[0])

        print("\nSlider of ages will be adjusted...")
        print("Minimum age will go ...")
        print("from {}% = {} years old".format(current_percentage_min,
                                               (current_percentage_min/percentage_per_year)+min_age_tinder))
        print("to {}% = {} years old".format(to_percentage_min, min))
        print("Maximum age will go ...")
        print("from {}% = {} years old".format(current_percentage_max,
                                               (current_percentage_max / percentage_per_year) + min_age_tinder))
        print("to {}% = {} years old".format(to_percentage_max, max))
        print("with a fault margin of 1%\n")
        tolerance = 10
        if abs(current_percentage_min - to_percentage_min) <= tolerance and abs(current_percentage_max - to_percentage_max) <= tolerance:
            print("Sliders are already within the acceptable range. No adjustment needed.\n\n")
            return
        # start adjusting the distance slider
        while abs(to_percentage_min - current_percentage_min) > 1 or abs(to_percentage_max - current_percentage_max) > 1:
            ac = ActionChains(self.browser)

            if current_percentage_min < to_percentage_min:
                ac.click_and_hold(btn_minage).move_by_offset(5, 0).release(btn_minage).perform()
            elif current_percentage_min > to_percentage_min:
                ac.click_and_hold(btn_minage).move_by_offset(-5, 0).release(btn_minage).perform()

            ac = ActionChains(self.browser)
            if current_percentage_max < to_percentage_max:
                ac.click_and_hold(btn_maxage).move_by_offset(5, 0).release(btn_maxage).perform()
            elif current_percentage_max > to_percentage_max:
                ac.click_and_hold(btn_maxage).move_by_offset(-5, 0).release(btn_maxage).perform()

            # update current percentage
            current_percentage_min = float(btn_minage.get_attribute('style').split(' ')[1].split('%')[0])
            current_percentage_max = float(btn_maxage.get_attribute('style').split(' ')[1].split('%')[0])

        print("Ended slider with ages from {} years old  to {} years old\n\n".format((current_percentage_min/percentage_per_year)+min_age_tinder,
              (current_percentage_max / percentage_per_year) + min_age_tinder))
        time.sleep(5)

    def set_sexualitiy(self, type):
        if not isinstance(type, Sexuality):
            assert False

        xpath = '//*[@href="/app/settings/gender"]/div/div/div/div'
        WebDriverWait(self.browser, self.delay).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        element = self.browser.find_element(By.XPATH, xpath)
        element.click()

        xpath = '//*[@aria-pressed="false"]'.format(type.value)
        WebDriverWait(self.browser, self.delay).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        elements = self.browser.find_elements(By.XPATH, xpath)

        for element in elements:
            if element.find_element(By.XPATH, './/div/label').text == type.value:
                element.click()
                break

        print("clicked on " + type.value)
        time.sleep(5)

    def set_global(self, boolean, language=None):
        # check if global is already activated
        # Global is activated when the href to preferred languages is visible
        is_activated = False
        try:
            xpath = '//*[@href="/app/settings/global/languages"]/div'
            WebDriverWait(self.browser, self.delay).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            self.browser.find_element(By.XPATH, xpath)
            is_activated = True

        except:
            pass

        if boolean != is_activated:
            xpath = '//*[@name="global"]'
            element = self.browser.find_element(By.XPATH, xpath)
            element.click()

        if is_activated and language:
            print("\nUnfortunately, Languages setting feature does not yet exist")
            print("If needed anyways:\nfeel free to open an issue and ask for the feature")
            print("or contribute by making a pull request.\n")

            '''
            languages_element.click()
            xpath = "//*[contains(text(), {})]".format(language)
            WebDriverWait(self.browser, self.delay).until(
                    EC.presence_of_element_located((By.XPATH, xpath)))
            self.browser.find_elements(By.XPATH, xpath).click()
            '''
            time.sleep(5)

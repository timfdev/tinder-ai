from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from logging import getLogger

logger = getLogger(__name__)


class MatchService:

    WEBDRIVER_WAIT_TIME = 10

    def __init__(self, browser):
        """
        Initialize the Matcher class.
        :param browser: The browser instance used for interaction.
        """
        self.browser = browser

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

    @staticmethod
    def extract_profile_details(match_element, browser, retry=3):
        """
        Extract the information of the current match.
        :param match_element: The WebElement representing the match to extract details from.
        :param browser: The WebDriver instance.
        :return: A dictionary containing the information of the current match.
        """
        from urllib.parse import urlparse
        try:
            # Click on the match element to open the profile
            logger.info("Clicking on match element to open profile...")
            match_element.click()
            time.sleep(1)

            # Define the XPath for the outer container that holds all profile information
            profile_content_xpath = "//div[contains(@class, 'profileContent')]"

            # Wait for the profile content container to become visible
            logger.info("Waiting for profile content container to become visible...")
            profile_content = WebDriverWait(browser, MatchService.WEBDRIVER_WAIT_TIME).until(
                EC.visibility_of_element_located((By.XPATH, profile_content_xpath))
            )

            logger.info("Profile content is visible. Extracting details...")

            # Prepare a dictionary to store extracted details
            profile_data = {}

            profile_data['match_id'] = urlparse(browser.current_url).path.split('/')[-1]

            # Extract Name and Age
            try:
                name_element = profile_content.find_element(
                    By.XPATH, ".//h1[contains(@class, 'Typs(display-2-strong)')]/span[1]"
                )
                age_element = profile_content.find_element(
                    By.XPATH, ".//h1[contains(@class, 'Typs(display-2-strong)')]/span[2]"
                )
                profile_data['name'] = name_element.text.strip()
                profile_data['age'] = int(age_element.text.strip()) if age_element.text.strip().isdigit() else None
            except NoSuchElementException:
                profile_data['name'] = None
                profile_data['age'] = None

            # Extract Bio
            try:
                bio_element = profile_content.find_element(
                    By.XPATH, ".//div[contains(@class, 'C($c-ds-text-primary) Typs(body-1-regular)')]"
                )
                profile_data['bio'] = bio_element.text.strip()
            except NoSuchElementException:
                profile_data['bio'] = None

            # Extract "Looking For"
            try:
                # Locate the "Looking for" section
                looking_for_section = profile_content.find_element(
                    By.XPATH, ".//div[contains(@class, 'P(24px)') and .//div[text()='Looking for']]"
                )

                # Extract main preference (e.g., "Long-term partner")
                main_preference = looking_for_section.find_element(
                    By.XPATH, ".//span[contains(@class, 'Typs(display-3-strong)')]"
                ).text.strip()

                # Store in profile_data
                profile_data['looking_for'] = main_preference
            except NoSuchElementException:
                profile_data['looking_for'] = None

            # Extract Location
            try:
                location_element = profile_content.find_element(
                    By.XPATH, ".//div[contains(@class, 'Typs(body-1-regular)') and contains(text(), 'Lives in')]/following-sibling::div"
                )
                profile_data['location'] = location_element.text.strip()
            except NoSuchElementException:
                profile_data['location'] = None

            # Extract Distance
            try:
                distance_element = profile_content.find_element(
                    By.XPATH, ".//div[contains(@class, 'D(b) W(100%)')]//div[contains(@class, 'Typs(body-1-regular)') and contains(text(), 'kilometers away')]"
                )
                profile_data['distance'] = distance_element.text.strip()
            except NoSuchElementException:
                profile_data['distance'] = None

            # Extract Essentials
            try:
                # Locate the "Essentials" header
                essentials_header = profile_content.find_element(
                    By.XPATH, "//div[contains(text(), 'Essentials')]/ancestor::div[contains(@class, 'P(24px)')]"
                )
                essentials_text = essentials_header.text.splitlines()

                # Remove the "Essentials" header text and keep the rest
                profile_data['essentials'] = essentials_text[1:] if len(essentials_text) > 1 else []
            except NoSuchElementException:
                profile_data['essentials'] = []

            # Extract Interests
            try:
                interests_elements = profile_content.find_elements(
                    By.XPATH, ".//div[contains(@class, 'passions')]//span[contains(@class, 'passions-shared')]"
                )
                profile_data['interests'] = [interest.text.strip() for interest in interests_elements]
            except NoSuchElementException:
                profile_data['interests'] = []

            # Extract Lifestyle
            try:
                # Locate the lifestyle section by its heading
                lifestyle_section = profile_content.find_element(
                    By.XPATH, ".//div[contains(@class, 'P(24px)') and .//div[text()='Lifestyle']]"
                )

                # Extract all lifestyle items
                lifestyle_items = lifestyle_section.find_elements(By.XPATH, ".//div[contains(@class, 'D(b) W(100%)')]")

                profile_data['lifestyle'] = {}
                for item in lifestyle_items:
                    try:
                        # Extract the category (e.g., Smoking, Workout)
                        category = item.find_element(By.XPATH, ".//h3[contains(@class, 'Typs(subheading-2)')]").text.strip()

                        # Extract the value (e.g., Non-smoker, Often)
                        value = item.find_element(By.XPATH, ".//div[contains(@class, 'Typs(body-1-regular)')]").text.strip()

                        # Store in the lifestyle dictionary
                        profile_data['lifestyle'][category] = value
                    except NoSuchElementException:
                        # Skip if any part of the item is missing
                        continue
            except NoSuchElementException:
                profile_data['lifestyle'] = {}

        except TimeoutException:
            logger.error("Profile content did not become visible in time.")
        except Exception as e:
            logger.error(f"Error occurred while extracting profile details: {e}")
        except StaleElementReferenceException:
            logger.error("Stale element reference occurred while extracting profile details.")
        finally:
            MatchService.close_match(browser)
        return profile_data

    @staticmethod
    def close_match(browser):
        """
        Close the match profile view and return to the matches list.
        :param driver: Selenium WebDriver instance.
        """
        try:
            # Wait for the close button to become visible
            close_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/app/matches'] div.close"))
            )
            # Click the close button
            close_button.click()
            logger.info("Closed the match profile.")
        except Exception as e:
            logger.error(f"Error closing the match profile: {e}")

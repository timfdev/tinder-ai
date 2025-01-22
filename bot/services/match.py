from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from undetected_chromedriver import Chrome
from shared.models import MatchProfile, Message

from logging import getLogger
import time
from urllib.parse import urlparse
from dataclasses import dataclass, field
from typing import Optional, List


logger = getLogger(__name__)


@dataclass
class Match:
    match_id: str
    browser: Chrome = field(default=None, repr=False)
    profile: MatchProfile = field(
        default_factory=lambda: MatchProfile(match_id="")
    )

    @classmethod
    def from_element(cls, element, browser, messages: bool = False) -> 'Match':
        """Create a Match instance from a DOM element.

        Args:
            element: The DOM element (either match or message element)
            browser: Chrome instance
            messages: If True, extract last messages before closing profile
        """
        match = None
        try:
            # Click the element to open profile
            element.click()
            time.sleep(1)

            # Wait for profile content
            profile_content = WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'profileContent')]")
                )
            )

            # Extract match data
            profile_data = {
                'match_id': urlparse(browser.current_url).path.split('/')[-1],
            }

            # Extract all profile info
            profile_data.update(cls._extract_basic_info(profile_content))
            profile_data.update(cls._extract_bio(profile_content))
            profile_data.update(cls._extract_looking_for(profile_content))
            profile_data.update(
                cls._extract_location_and_distance(profile_content)
            )
            profile_data.update(cls._extract_essentials(profile_content))
            profile_data.update(cls._extract_interests(profile_content))
            profile_data.update(cls._extract_lifestyle(profile_content))

            # If messages flag is True, extract last messages
            if messages:
                logger.debug("Getting last messages")
                chat_content = WebDriverWait(browser, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH,
                         "//div[contains(@aria-label, 'Conversation history')]"
                         )
                    )
                )

                profile_data['last_messages'] = cls._extract_last_messages(
                    chat_content
                )

            # Create profile and match instance
            profile = MatchProfile(**profile_data)
            match = cls(
                match_id=profile.match_id,
                browser=browser,
                profile=profile
            )

            return match

        except Exception as e:
            logger.error(f"Error creating match from element: {e}")
            return cls(match_id="unknown", browser=browser)

    def send_opener(self, message: str, mock: bool) -> bool:
        """
        Send an opener to the match.
        """
        return self._send_message(message=message, mock=mock, context="opener")

    def send_reply(self, message: str, mock: bool) -> bool:
        """
        Send a reply to the match.
        """
        return self._send_message(message=message, mock=mock, context="reply")

    def navigate_to_chat(self) -> None:
        """Navigate to the chat window with this match."""
        try:
            chat_url = f"https://tinder.com/app/messages/{self.match_id}"
            self.browser.get(chat_url)
        except Exception as e:
            logger.error(f"Error navigating to chat: {e}")

    def close_profile(self) -> None:
        """Close the match profile view."""
        try:
            close_button = WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a[href='/app/matches'] div.close")
                )
            )
            close_button.click()
            logger.debug(f"Closed profile for {self.profile.name}")
        except Exception as e:
            logger.error(f"Error closing profile: {e}")

    def _send_message(self, message: str, mock: bool, context: str) -> bool:
        """
        Send a message (opener or reply) to the match,
        or log it if mock is True.

        :param message: The text to send.
        :param mock:
            If True, log only (no sending).
            If False, send the message.
        :param context: "opener" or "reply" (used for logging).
        :return: True if successful or mock, False if an error occurred.
        """
        if mock:
            logger.info(
                f"[MOCK] Would send {context} to {self.profile.name}: {message}"
            )
            return True

        try:
            # Wait for the input field to be present
            message_input = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//textarea[@placeholder='Type a message']")
                )
            )

            # Use JavaScript to inject the full message (including emojis)
            JS_ADD_TEXT_TO_INPUT = """
                var textarea = arguments[0], txt = arguments[1];
                textarea.value = txt;  // Set the value
                textarea.dispatchEvent(new Event('input', { bubbles: true }));  // Trigger input event
                textarea.dispatchEvent(new Event('change', { bubbles: true }));  // Trigger change event
            """
            self.browser.execute_script(JS_ADD_TEXT_TO_INPUT, message_input, message)

            # Click on the input field to activate it
            message_input.click()

            # Simulate typing a single letter to trigger events
            message_input.send_keys("x")  # Type a placeholder character
            message_input.send_keys(Keys.BACKSPACE)  # Remove the placeholder character

            # Press Enter to send the message
            message_input.send_keys(Keys.RETURN)

            logger.info(
                f"{context.capitalize()} sent to {self.profile.name}: {message}"
            )
            time.sleep(1.5)
            return True
        except Exception as e:
            logger.error(
                f"Error sending {context} to {self.profile.name}: {e}"
            )
            return False

    @staticmethod
    def _extract_last_messages(chat_content) -> Optional[List[Message]]:
        """Extract last few messages from conversation"""
        try:
            messages = []
            # Find all message helper containers
            msg_helpers = chat_content.find_elements(
                By.CLASS_NAME, "msgHelper"
            )

            # Process each message helper
            for helper in msg_helpers:
                try:
                    # Find the message container
                    msg_div = helper.find_element(By.CLASS_NAME, "msg")

                    # Get the text content
                    text_element = msg_div.find_element(By.CLASS_NAME, "text")
                    message = text_element.text.strip()

                    # Skip empty messages
                    if not message:
                        continue

                    # Get parent div to check alignment
                    parent = helper.find_element(By.XPATH, "./parent::div")
                    parent_classes = parent.get_attribute('class')

                    # Ta(start) indicates received message
                    is_received = 'Ta(start)' in (parent_classes or '')

                    messages.append(
                        Message(
                            message=message,
                            is_received=is_received
                        )
                    )

                except NoSuchElementException:
                    continue

            return messages if messages else None

        except Exception as e:
            logger.error(f"Error extracting messages: {e}")
            return None

    @staticmethod
    def _extract_basic_info(profile_content) -> dict:
        """Extract name and age."""
        data = {'name': None, 'age': None}
        try:
            name_element = profile_content.find_element(
                By.XPATH,
                ".//h1[contains(@class, 'Typs(display-2-strong)')]/span[1]"
            )
            age_element = profile_content.find_element(
                By.XPATH,
                ".//h1[contains(@class, 'Typs(display-2-strong)')]/span[2]"
            )
            data['name'] = name_element.text.strip()
            data['age'] = int(
                age_element.text.strip()
            ) if age_element.text.strip().isdigit() else None
        except NoSuchElementException:
            logger.debug("Could not find name/age elements")
        return data

    @staticmethod
    def _extract_bio(profile_content) -> dict:
        """Extract bio."""
        try:
            bio_element = profile_content.find_element(
                By.XPATH,
                ".//div[contains(@class, "
                "'C($c-ds-text-primary) Typs(body-1-regular)')]"
            )
            return {'bio': bio_element.text.strip()}
        except NoSuchElementException:
            logger.debug("Could not find bio element")
            return {'bio': None}

    @staticmethod
    def _extract_looking_for(profile_content) -> dict:
        """Extract 'Looking For'."""
        try:
            looking_for_section = profile_content.find_element(
                By.XPATH,
                ".//div[contains(@class, 'P(24px)') and "
                ".//div[text()='Looking for']]"
            )
            main_preference = looking_for_section.find_element(
                By.XPATH,
                ".//span[contains(@class, "
                "'Typs(display-3-strong)')]"
            ).text.strip()
            return {'looking_for': main_preference}
        except NoSuchElementException:
            logger.debug("Could not find 'Looking For' element")
            return {'looking_for': None}

    @staticmethod
    def _extract_location_and_distance(profile_content) -> dict:
        """Extract location and distance."""
        data = {'location': None, 'distance': None}
        try:
            location_element = profile_content.find_element(
                By.XPATH,
                ".//div[contains(@class, 'Typs(body-1-regular)') "
                "and contains(text(), 'Lives in')]/following-sibling::div"
            )
            data['location'] = location_element.text.strip()
        except NoSuchElementException:
            logger.debug("Could not find location element")

        try:
            distance_element = profile_content.find_element(
                By.XPATH,
                ".//div[contains(@class, 'D(b) W(100%)')]"
                "//div[contains(@class, 'Typs(body-1-regular)') and "
                "contains(text(), 'kilometers away')]"
            )
            data['distance'] = distance_element.text.strip()
        except NoSuchElementException:
            logger.debug("Could not find distance element")
        return data

    @staticmethod
    def _extract_essentials(profile_content) -> dict:
        """Extract essentials."""
        try:
            essentials_header = profile_content.find_element(
                By.XPATH,
                "//div[contains(text(), 'Essentials')]"
                "/ancestor::div[contains(@class, 'P(24px)')]"
            )
            essentials_text = essentials_header.text.splitlines()
            essentials = (
                essentials_text[1:] if len(essentials_text) > 1 else []
            )
            return {'essentials': essentials}
        except NoSuchElementException:
            logger.debug("Could not find essentials element")
            return {'essentials': []}

    @staticmethod
    def _extract_interests(profile_content) -> dict:
        """Extract interests."""
        try:
            interests_elements = profile_content.find_elements(
                By.XPATH,
                ".//div[contains(@class, 'passions')]"
                "//span[contains(@class, 'passions-shared')]"
            )
            interests = [
                interest.text.strip()
                for interest in interests_elements
            ]
            return {'interests': interests}
        except NoSuchElementException:
            logger.debug("Could not find interests element")
            return {'interests': []}

    @staticmethod
    def _extract_lifestyle(profile_content) -> dict:
        """Extract lifestyle."""
        try:
            lifestyle_section = profile_content.find_element(
                By.XPATH,
                ".//div[contains(@class, 'P(24px)') "
                "and .//div[text()='Lifestyle']]"
            )
            lifestyle_items = lifestyle_section.find_elements(
                By.XPATH,
                ".//div[contains(@class, 'D(b) W(100%)')]"
            )
            lifestyle = {}
            for item in lifestyle_items:
                try:
                    category = item.find_element(
                        By.XPATH,
                        ".//h3[contains(@class, 'Typs(subheading-2)')]"
                    ).text.strip()
                    value = item.find_element(
                        By.XPATH,
                        ".//div[contains(@class, 'Typs(body-1-regular)')]"
                    ).text.strip()
                    lifestyle[category] = value
                except NoSuchElementException:
                    continue
            return {'lifestyle': lifestyle}
        except NoSuchElementException:
            logger.debug("Could not find lifestyle element")
            return {'lifestyle': {}}

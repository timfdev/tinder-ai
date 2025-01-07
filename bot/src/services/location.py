import requests
from logging import getLogger
from typing import Tuple, Optional

logger = getLogger(__name__)


class LocationService:
    def __init__(self, browser, settings) -> None:
        """
        Initialize the LocationService with a browser instance and settings.

        :param browser: Selenium WebDriver instance (e.g., Chrome).
        :param settings: Settings instance containing coordinates, proxy, etc.
        """
        self.browser = browser
        self.settings = settings
        self.proxy_url = settings.proxy_url

    def get_public_ip(self) -> str:
        """
        Fetch the public IP address using ipinfo.io.

        :return: Public IP address as a string, or None if unable to fetch.
        """
        proxies = {
            "http": self.proxy_url,
            "https": self.proxy_url
        } if self.proxy_url else None

        try:
            response = requests.get(
                "https://ipinfo.io/json",
                proxies=proxies,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("ip")
            else:
                logger.info(
                    f"Unable to fetch IP. Status Code: {response.status_code}"
                )
        except Exception as e:
            logger.info(f"Exception while fetching IP via requests: {e}")

        return None

    def get_coordinates_from_ip(
        self, ip_address
    ) -> Optional[Tuple[float, float]]:
        """
        Get latitude and longitude for a given IP address using ipinfo.io.

        :param ip_address: IP address to fetch coordinates for.
        :return: Tuple of (latitude, longitude) or None if unable to fetch.
        """
        proxies = {
            "http": self.proxy_url,
            "https": self.proxy_url
        } if self.proxy_url else None

        try:
            url = f"https://ipinfo.io/{ip_address}/geo"
            response = requests.get(url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                data = response.json()
                loc = data.get("loc")
                if loc:
                    lat_str, lon_str = loc.split(",")
                    return float(lat_str), float(lon_str)
                else:
                    logger.info(
                        "'loc' field not found in ipinfo response. "
                        f"Data: {data}"
                    )
            else:
                logger.info(
                    "Unable to fetch geo data. "
                    f"Status Code: {response.status_code}"
                )
        except Exception as e:
            logger.info(f"Exception while fetching coordinates: {e}")

        return None

    def set_custom_location(
        self, latitude, longitude, accuracy="100%"
    ) -> None:
        """
        Set a custom geolocation in the browser using Chrome DevTools Protocol.

        :param latitude: Latitude to set.
        :param longitude: Longitude to set.
        :param accuracy: Accuracy percentage (default is "100%").
        """
        try:
            accuracy_value = int(accuracy.rstrip('%'))
        except ValueError:
            accuracy_value = 100

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": accuracy_value
        }
        self.browser.execute_cdp_cmd("Page.setGeolocationOverride", params)
        logger.info(
            f"Browser geolocation set to: "
            f"lat={latitude}, lon={longitude}, acc={accuracy_value}%"
        )

    def configure_location(self) -> None:
        """
        Configure the browser's geolocation based on settings or proxy.

        1. Use provided coordinates if available.
        2. If a proxy is set, fetch the public IP and coordinates,
           then set them.
        3. Skip if no data is available.
        """
        lat, lon = self.settings.location_lat, self.settings.location_lon
        if lat and lon:
            logger.info(f"Using provided coordinates: {lat}, {lon}")
            self.set_custom_location(lat, lon)
            return

        if self.proxy_url:
            ip_address = self.get_public_ip()
            if ip_address:
                coords = self.get_coordinates_from_ip(ip_address)
                if coords:
                    lat, lon = coords
                    logger.info(
                        "Setting location based on proxy "
                        f"IP coords: {lat}, {lon}"
                    )
                    self.set_custom_location(lat, lon)
                    return
                else:
                    logger.info(
                        "Could not retrieve coordinates from ipinfo.io."
                    )
            else:
                logger.info("Could not retrieve IP via ipinfo.io/json.")
        else:
            logger.info("No proxy configured and no coordinates provided.")

        logger.info("Skipping custom geolocation override.")

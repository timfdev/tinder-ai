import requests


class LocationSetter:
    def __init__(self, browser, settings, local_proxy_url=None):
        """
        :param browser: The Selenium WebDriver instance (Chrome, etc.).
        :param settings: Your Settings instance containing (optional) coordinates, proxy, etc.
        :param local_proxy_url: URL of the local proxy server, e.g. "http://localhost:3128".
                                If provided, we will route our requests through it.
        """
        self.browser = browser
        self.settings = settings
        self.local_proxy_url = local_proxy_url

    def get_public_ip(self):
        """
        Fetch public IP via requests to https://ipinfo.io/json,
        optionally using the local proxy if provided.
        """
        # If local_proxy_url is provided, route the requests through it
        proxies = {
            "http": self.local_proxy_url,
            "https": self.local_proxy_url
        } if self.local_proxy_url else None

        try:
            response = requests.get("https://ipinfo.io/json", proxies=proxies, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("ip")
            else:
                print(f"[LocationSetter] Unable to fetch IP. Status Code: {response.status_code}")
        except Exception as e:
            print(f"[LocationSetter] Exception while fetching IP via requests: {e}")

        return None

    def get_coordinates_from_ip(self, ip_address):
        """
        Get latitude/longitude for the given IP address using https://ipinfo.io/<ip>/geo.
        Again, we use the local proxy if specified.
        """
        proxies = {
            "http": self.local_proxy_url,
            "https": self.local_proxy_url
        } if self.local_proxy_url else None

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
                    print(f"[LocationSetter] 'loc' field not found in ipinfo response. Data: {data}")
            else:
                print(f"[LocationSetter] Unable to fetch geo data. Status Code: {response.status_code}")
        except Exception as e:
            print(f"[LocationSetter] Exception while fetching coordinates: {e}")

        return None

    def set_custom_location(self, latitude, longitude, accuracy="100%"):
        """
        Sets a custom geolocation in the browser via Chrome DevTools Protocol.
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
        print(f"[LocationSetter] Browser geolocation set to: lat={latitude}, lon={longitude}, acc={accuracy_value}%")

    def configure_location(self):
        """
        1. If settings.coordinates is provided, use that directly.
        2. Otherwise, if settings.proxy is set, we attempt to find
           the proxy IP via requests (through local_proxy_url if any),
           then fetch coordinates from ipinfo.io, and set them.
        3. If nothing is provided, skip.
        """
        lat, lon = self.settings.location_lat, self.settings.location_lon
        # 1) If explicit coordinates exist, just set them
        if lat and lon:
            print(f"[LocationSetter] Using provided coordinates: {lat}, {lon}")
            self.set_custom_location(lat, lon)
            return

        # 2) If we have a proxy set, we try to get the public IP and then coords
        if self.local_proxy_url:
            ip_address = self.get_public_ip()
            if ip_address:
                coords = self.get_coordinates_from_ip(ip_address)
                if coords:
                    lat, lon = coords
                    print(f"[LocationSetter] Setting location based on proxy IP coords: {lat}, {lon}")
                    self.set_custom_location(lat, lon)
                    return
                else:
                    print("[LocationSetter] Could not retrieve coordinates from ipinfo.io.")
            else:
                print("[LocationSetter] Could not retrieve IP via ipinfo.io/json.")
        else:
            print("[LocationSetter] No proxy configured and no coordinates provided.")

        # If we haven't returned by now, it means we failed or had no data.
        print("[LocationSetter] Skipping custom geolocation override.")

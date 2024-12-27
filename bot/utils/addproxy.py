from bot.settings import Proxy
from pathlib import Path
import os


def get_proxy_extension(proxy: Proxy, proxy_folder=None) -> Path:
    manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
    """

    background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
    """ % (
        proxy.host,
        proxy.port,
        proxy.user,
        proxy.pwd
    )

    if proxy_folder is None:
        proxy_folder = Path(__file__).parent / "extension"

    # Ensure the extension directory exists
    os.makedirs(proxy_folder, exist_ok=True)

    # Always overwrite manifest.json and background.js to ensure updates
    with open(f"{proxy_folder}/manifest.json", "w") as f:
        f.write(manifest_json)

    with open(f"{proxy_folder}/background.js", "w") as f:
        f.write(background_js)

    return proxy_folder

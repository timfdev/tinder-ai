

class Matcher:
    def __init__(self, browser):
        self.browser = browser

    def match(self, text):
        return self.pattern in text

    def get_response(self):
        return self.response
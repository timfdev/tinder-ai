<p align="center">
    <img src="static/tinder.svg" align="center" width="30%">
</p>
<p align="center"><h1 align="center">TINDER-AI</h1></p>
<p align="center">
	<em><code>❯ Build an AI dating bot</code></em>
</p>
<p align="center">
	<!-- local repository, no metadata badges. --></p>
<p align="center">
	<img src="https://img.shields.io/badge/Selenium-43B02A.svg?style=default&logo=Selenium&logoColor=white" alt="Selenium">
	<img src="https://img.shields.io/badge/-OpenAI%20API-eee?style=flat-square&logo=openai&logoColor=412991" alt="OpenAI">
	<br>
	<img src="https://img.shields.io/badge/Python-3776AB.svg?style=default&logo=Python&logoColor=white" alt="Python">
	<img src="https://img.shields.io/badge/Poetry-60A5FA.svg?style=default&logo=Poetry&logoColor=white" alt="Poetry">
	<img src="https://img.shields.io/badge/Pydantic-E92063.svg?style=default&logo=Pydantic&logoColor=white" alt="Pydantic">
</p>
<br>

## 📌 Table of Contents
- [Overview](#-overview)
- [Setup](#-setup)
- [Usage](#-usage)
  - [Session](#-session)
  - [Openers](#-openers)
  - [Replies](#-replies)
  - [Auto-Swiping](#-auto-swiping)
- [Messenger Service](#-messenger-service)
- [Disclaimer](#-disclaimer)

---

## 🚀 Overview
Tinder-AI is a **Tinder bot SDK** using **Selenium with undetected Chromedriver**. It provides:
- **Profile setup**
- **Proxy support**
- **Geolocation spoofing**
- **Automated swiping**
- **Chatbot integration (Openers & replies)**

Use it to build your own **AI dating assistant**.

---

## ⚙️ Setup

**Install the package**
```shell
pip install tinder-ai
```

**Copy the `.env.example` file to `.env`:**
```sh
cp .env.example .env
```

Edit .env and fill in the required values.

---

## 🛠 Usage
#### Session: Set up a session
```python
from tinder_ai import Settings, Session

settings = Settings()
messenger_service = MockMessengerService()
with Session(
	settings=settings,
	messenger_service=messenger_service
) as session:
	session.login(
		method=settings.get_login_method()
	)
```

#### Openers: Send a first message to all matches
```python
session.handle_matches()
```

#### Replies: Auto-reply unread messages
```python
session.handle_unread_messages()
```

#### Auto-Swiping: Swipe on profiles automatically
```python
session.start_swiping()
```

### Messenger Service

##### Option 1: Using an API
Plug in your own LLM service to use for messaging.
```python
messenger_service = MessengerService(
	base_url="http://0.0.0.0:8080"
)
session = Session(
	settings=settings,
	messenger_service=messenger_service
)
```

##### Option 2: Using a custom class
Inherit from the base messenger class similar to the `MockMessengerService`
```python
class MockMessengerService(BaseMessengerService):
    """A fallback implementation of the Messenger Service."""
    def generate_opener(self, profile: MatchProfile) -> MessageResponse:
        """Generate a default opening message."""
        return MessageResponse(message=f"Hi {profile.name} 😊!")

    def generate_reply(
        self,
        profile: MatchProfile,
        last_messages: Optional[List[Message]] = None
    ) -> MessageResponse:
        """Generate an empty reply."""
        raise NotImplementedError("Reply is not implemented")

```

---
## ⚠️ Disclamer

**Automation is against Tinder's TOS.**

This project is for **educational purposes only**.
You are responsible for any consequences, including account bans or legal actions.

---
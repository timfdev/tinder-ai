import enum
from dataclasses import dataclass


@dataclass
class SessionData:
    duration: int = 0
    likes: int = 0
    dislikes: int = 0
    superlikes: int = 0
    matches: int = 0

    sent_openings: int = 0
    sent_replies: int = 0

    def __str__(self):
        return (
            f"  Session:\n"
            f"   Duration   : {self.duration} seconds\n"
            f"   Likes      : {self.likes}\n"
            f"   Dislikes   : {self.dislikes}\n"
            f"   Superlikes : {self.superlikes}\n"
            f"   Matches    : {self.matches}\n\n"
            f"  Messages\n"
            f"   Openings   : {self.sent_openings}\n"
            f"   Replies    : {self.sent_replies}\n\n"
        )


class LoginMethods(enum.Enum):
    FACEBOOK = "facebook"
    GOOGLE = "google"


class Sexuality(enum.Enum):
    MEN = "Men"
    WOMEN = "Women"
    EVERYONE = "Everyone"

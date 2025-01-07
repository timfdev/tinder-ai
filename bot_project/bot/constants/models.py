import enum
from dataclasses import dataclass


@dataclass
class SessionData:
    duration: int = 0
    likes: int = 0
    dislikes: int = 0
    superlikes: int = 0
    matches: int = 0


class LoginMethods(enum.Enum):
    FACEBOOK = "facebook"
    GOOGLE = "google"


class Socials(enum.Enum):
    SNAPCHAT = "snapchat"
    INSTAGRAM = "instagram"
    PHONENUMBER = "phone"
    FACEBOOK = "facebook"


class Sexuality(enum.Enum):
    MEN = "Men"
    WOMEN = "Women"
    EVERYONE = "Everyone"


class Language(enum.Enum):
    ENGLISH = "English"
    AFRIKAANS = "Afrikaans"
    ARABIC = "Arabic"
    BULGARIAN = "Bulgarian"
    BOSNIAN = "Bosnian"
    CROATIAN = "Croatian"
    CZECH = "Czech"
    DANISH = "Danish"
    DUTCH = "Dutch"
    ESTONIAN = "Estonian"
    FINNISH = "Finnish"
    FRENCH = "French"
    GEORGIAN = "Georgian"
    GERMAN = "German"
    GREEK = "Greek"
    HINDI = "Hindi"
    HUNGARIAN = "Hungarian"
    INDONESIAN = "Indonesian"
    ITALIAN = "Italian"
    JAPANESE = "Japanese"
    KOREAN = "Korean"
    LATVIAN = "Latvian"
    LITHUANIAN = "Lithuanian"
    MACEDONIAN = "Macedonian"
    MALAY = "Malay"
    POLISH = "Polish"
    PORTUGUESE = "Portuguese"
    ROMANIAN = "Romanian"
    RUSSIAN = "Russian"
    SERBIAN = "Serbian"
    SPANISH = "Spanish"
    SLOVAK = "Slovak"
    SLOVENIAN = "Slovenian"
    SWEDISH = "Swedish"
    TAMIL = "Tamil"
    THAI = "Thai"
    TURKISH = "Turkish"
    UKRAINIAN = "Ukrainian"
    VIETNAMESE = "Vietnamese"

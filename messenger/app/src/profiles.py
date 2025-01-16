from shared.models import MatchProfile

_MAIN_PROFILE_DATA = {
    "match_id": "me123",
    "name": "Tim",
    "age": 30,
    "bio": (
        "Tech enthusiast who loves coding and outdoor adventures.",
        "Always up for trying new restaurants and coffee shops."
    ),
    "interests": ["programming", "hiking", "coffee", "technology"],
    "looking_for": "Someone to share adventures and deep conversations with",
    "location": "New York",
    "distance": "5 miles",
    "essentials": ["Tech-savvy", "Active"],
    "lifestyle": {"diet": "Coffee addict", "exercise": "Regular"}
}

personal_profile = MatchProfile(**_MAIN_PROFILE_DATA)

import logging
from typing import Dict, Optional, List
from langchain_community.tools import tool
import googlemaps
from dotenv import load_dotenv
import os
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)
load_dotenv()


class PlaceType(str, Enum):
    """Allowed types in Places API that make sense."""
    AMUSEMENT_PARK = "amusement_park"
    AQUARIUM = "aquarium"
    ART_GALLERY = "art_gallery"
    BAKERY = "bakery"
    BAR = "bar"
    BOWLING_ALLEY = "bowling_alley"
    CAFE = "cafe"
    GYM = "gym"
    LIBRARY = "library"
    MOVIE_THEATER = "movie_theater"
    MUSEUM = "museum"
    NIGHT_CLUB = "night_club"
    PARK = "park"
    RESTAURANT = "restaurant"
    SHOPPING_MALL = "shopping_mall"
    SPA = "spa"
    STADIUM = "stadium"
    ZOO = "zoo"


@dataclass
class Coordinates:
    lat: float
    lng: float


def get_coordinates() -> Coordinates:
    """Get the current coordinates of the user."""
    # This function would normally use a location service to get the user's coordinates
    return Coordinates(lat=3.160550, lng=101.739536)


@tool(parse_docstring=True)
def lookup_places(venue_type: PlaceType, radius: int = 10000) -> Optional[List[Dict]]:
    """Look up venue suggestions near your location.

    Args:
        venue_type: Type of venue to look for
        radius: Search radius in meters (default 10000m)

    Returns:
        List of top 3 venues with their names and areas, or None if not found
    """
    try:
        coords = get_coordinates()
        gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))

        places_result = gmaps.places_nearby(
            location=(coords.lat, coords.lng),
            radius=radius,
            type=venue_type.value
        )

        if not places_result.get('results'):
            logger.info(f"No {venue_type}s found within {radius}m")
            return None

        # Sort by rating and get top 3
        sorted_places = sorted(
            places_result['results'],
            key=lambda x: (x.get('rating', 0), x.get('user_ratings_total', 0)),
            reverse=True
        )[:3]

        return [place.get('name') for place in sorted_places]

    except ValueError as e:
        logger.error(f"Invalid venue_type: {str(e)}")
        raise ValueError("Invalid venue_type provided.")

    except Exception as e:
        logger.error(f"Error looking up places: {str(e)}")
        return None


@tool(parse_docstring=True)
def get_place_details(name: str, area: str) -> Optional[Dict]:
    """Look up details about a specific place that was mentioned.

    Args:
        name: Name of the place
        area: Area or vicinity of the place (e.g., neighborhood, street)

    Returns:
        Dict with place details or None if not found
    """
    try:
        gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))

        # Search for the specific place
        places = gmaps.find_place(
            input=f"{name} {area}",
            input_type="textquery",
            fields=["place_id", "name", "formatted_address", "opening_hours", "rating"]
        )

        if not places.get('candidates'):
            logger.info(f"Could not find place: {name} in {area}")
            return None

        place_id = places['candidates'][0]['place_id']
        details = gmaps.place(place_id)['result']

        return {
            'name': details.get('name'),
            'area': details.get('vicinity'),
            'rating': details.get('rating')
        }

    except Exception as e:
        logger.error(f"Error getting place details: {str(e)}")
        return None


if __name__ == "__main__":
    # Test the lookup_places tool
    venue = lookup_places({"venue_type": "bar", "radius": "5000"})
    if venue:
        logger.info(f"Best restaurant near you: {venue['name']} in {venue['area']}")

    print(venue)
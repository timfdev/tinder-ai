

from bot.session import Session
from bot.constants.models import (
    LoginMethods,
    Socials,
    Sexuality,
    Language,
)
from bot.settings import Settings
import time


if __name__ == "__main__":
    # Load settings
    settings = Settings()

    # creates instance of session
    with Session(settings=settings, use_local_proxy_server=True) as session:

        session.login(LoginMethods.FACEBOOK)
        session.set_preferences()
        time.sleep(2000)
    exit()
    # session.dislike(amount=1)
    # session.superlike(amount=1)

    # adjust allowed distance for geomatches
    # Note: PARAMETER IS IN KILOMETERS!
    session.set_distance_range(km=15)

    # set range of prefered age
    session.set_age_range(18, 55)

    # set interested in gender(s) -> options are: WOMEN, MEN, EVERYONE
    session.set_sexuality(Sexuality.WOMEN)

    # Allow profiles from all over the world to appear
    # session.set_global(True)

    # Getting matches takes a while, so recommended you load as much as possible from local storage
    # get new matches, with whom you haven't interacted yet
    # Let's load the first 10 new matches to interact with later on.
    # quickload on false will make sure ALL images are stored, but this might take a lot more time
    new_matches = session.get_new_matches(amount=10, quickload=False)
    print(new_matches)
    exit()
    # get already interacted with matches (matches with whom you've chatted already)
    messaged_matches = session.get_messaged_matches()

    # you can store the data and images of these matches now locally in data/matches
    # For now let's just store the messaged_matches
    for match in messaged_matches:
        session.store_local(match)

    # Pick up line with their personal name so it doesn't look spammy
    pickup_line = "Hey {}! You. Me. Pizza? Or do you not like pizza?"

    # loop through my new matches and send them the first message of the conversation
    for match in new_matches:
        # store name and chatid in variables so we can use it more simply later on
        name = match.get_name()
        id = match.get_chat_id()

        print(name, id)

        # # Format the match her/his name in your pickup line for a more personal approach.
        # message = pickup_line.format(name)

        # # send pick up line with their name in it to all my matches
        # session.send_message(chatid=id, message=message)

        # # # send a funny gif
        # # session.send_gif(chatid=id, gifname="")

        # # # send a funny song
        # # session.send_song(chatid=id, songname="")

        # # # send instagram or other socials like facebook, phonenumber and snapchat
        # # session.send_socials(chatid=id, media=Socials.INSTAGRAM, value="Fredjemees")

        # you can also unmatch
        #session.unmatch(chatid=id)

    # # let's scrape some geomatches now
    # for _ in range(5):
    #     # get profile data (name, age, bio, images, ...)
    #     geomatch = session.get_geomatch(quickload=False)
    #     # store this data locally as json with reference to their respective (locally stored) images
    #     session.store_local(geomatch)
    #     # dislike the profile, so it will show us the next geomatch (since we got infinite amount of dislikes anyway)
    #     session.dislike()

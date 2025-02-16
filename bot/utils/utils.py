import random
import time


MIN_SLEEP = 1.1
MAX_SLEEP = 2.6
BANNER = str(
    "\n\n╔═══════════════════════════════════════════════╗\n"
    "║                  tinder-ai                    ║\n"
    "║                                               ║\n"
    "║ GitHub:                                       ║\n"
    "║ https://github.com/timfdev/tinder-ai          ║\n"
    "╚═══════════════════════════════════════════════╝\n\n"
)


def random_sleep(
    min_sleep: float = MIN_SLEEP,
    max_sleep: float = MAX_SLEEP
) -> float:
    """
    Sleep for a random duration between MIN_SLEEP and MAX_SLEEP
    and return the sleep time
    """
    sleep_time = random.uniform(min_sleep, max_sleep)
    time.sleep(sleep_time)
    return sleep_time

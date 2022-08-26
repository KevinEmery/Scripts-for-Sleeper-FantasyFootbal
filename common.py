import re

from enum import Enum
from typing import List

from library.model.league import League


class PlatformSelection(Enum):
    SLEEPER = 1
    FLEAFLICKER = 2

def filter_leagues_by_league_name(leagues: List[League],
                                  name_regex: re.Pattern) -> List[League]:
    filtered_leagues = []

    for league in leagues:
        if name_regex.match(league.name):
            filtered_leagues.append(league)

    return filtered_leagues
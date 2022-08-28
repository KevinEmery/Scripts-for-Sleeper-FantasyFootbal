import requests

from typing import Any, Dict, List

from ...model.user import User

BASE_URL = "https://www.fleaflicker.com/api/"


def fetch_user_leagues(user: User, year: str) -> List[str]:
    request_url = BASE_URL + "FetchUserLeagues?sport=NFL&season={year}".format(
        year=year)

    if user.user_id != "":
        request_url += "&user_id={id}".format(id=user.user_id)
    elif user.email != "":
        request_url += "&email={email}".format(email=user.email)
    else:
        raise Exception("User {user} must have either id or email set".format(
            user.name))

    response = requests.get(request_url)
    return response.json()["leagues"]


def fetch_league_standings(league_id: str, year: str) -> List[str]:
    request_url = BASE_URL + "FetchLeagueStandings?sport=NFL&league_id={league_id}&season={year}".format(
        league_id=league_id, year=year)

    response = requests.get(request_url)
    return response.json()


def fetch_league_draft_board(league_id: str, year: str) -> List[str]:
    request_url = BASE_URL + "FetchLeagueDraftBoard?sport=NFL&season={year}&league_id={league_id}".format(
        year=year, league_id=league_id)

    response = requests.get(request_url)
    return response.json()


def fetch_trades(league_id: str) -> List[str]:
    request_url = BASE_URL + "FetchTrades?sport=NFL&league_id={league_id}&filter=TRADES_COMPLETED".format(
        league_id=league_id)

    response = requests.get(request_url)
    return response.json()["trades"]


def fetch_league_scoreboard(league_id: str, week: int, year: str):
    request_url = BASE_URL + "FetchLeagueScoreboard?sport=NFL&league_id={league_id}&scoring_period={week}&season={year}".format(
        league_id=league_id, week=str(week), year=year)

    response = requests.get(request_url)
    return response.json()
from datetime import datetime
from typing import Dict, List

import re

from . import api

from ..platform import Platform

from ... import defaults
from ...model.draftedplayer import DraftedPlayer
from ...model.league import League
from ...model.player import Player
from ...model.seasonscore import SeasonScore
from ...model.team import Team
from ...model.trade import Trade
from ...model.tradedetail import TradeDetail
from ...model.user import User
from ...model.weeklyscore import WeeklyScore


class Fleaflicker(Platform):
    def __init__(self):
        self._league_id_to_team_id_to_user: Dict[str, Dict[int, User]] = {}

    def get_admin_user_by_identifier(self, identifier: str) -> User:
        # Fleaflicker doesn't require you to query by Admin User Id, instead
        # making it available via email. Construct a dummy user object here solely
        # comprised of their email
        return User("", "Admin User", identifier)

    def get_all_leagues_for_user(
        self,
        user: User,
        year: str = defaults.YEAR,
        name_regex: re.Pattern = re.compile(".*")
    ) -> List[League]:
        leagues = []

        # Even when pulling past data, we can only check the current year's leagues.
        raw_league_list = api.fetch_user_leagues(user, defaults.YEAR)

        for raw_league in raw_league_list:
            league = League(raw_league["name"], raw_league["capacity"],
                            str(raw_league["id"]))

            if name_regex.match(league.name):
                self._store_team_and_user_data_for_league(
                    league.league_id, year)
                leagues.append(league)

        return leagues

    def get_drafted_players_for_league(
            self,
            league: League,
            year: str = defaults.YEAR) -> List[DraftedPlayer]:
        drafted_players = []

        raw_draft_board = api.fetch_league_draft_board(league.league_id, year)
        raw_rosters = raw_draft_board["rosters"]
        for roster in raw_rosters:
            for lineup_entry in roster["lineup"]:
                if "player" in lineup_entry:
                    player_data = lineup_entry["player"]["proPlayer"]

                    player = self._build_player_from_pro_player(player_data)

                    draft_position = lineup_entry["draftedAt"]["overall"]

                    drafted_players.append(
                        DraftedPlayer(player, draft_position))

        return drafted_players

    def get_all_trades_for_league(self, league: League) -> List[Trade]:
        all_trades = []

        team_id_to_user = self._league_id_to_team_id_to_user[league.league_id]
        raw_trades = api.fetch_trades(league.league_id)

        for trade_data in raw_trades:
            trade_time = datetime.fromtimestamp(
                int(trade_data["approvedOn"]) / 1000)

            # Ignore trades not made this year, Fleaflicker's API returns all trades throughout time
            if str(trade_time.year) != defaults.YEAR:
                continue

            trade_details = []

            for team_data in trade_data["teams"]:
                team_id = str(team_data["team"]["id"])
                user = team_id_to_user[team_id]

                team = Team(team_id, user,
                            self._build_roster_link(league.league_id, team_id))

                trade_detail = TradeDetail(team)

                # Fleaflicker's API doesn't return who you gave up in the
                # trade, just who you added or released to waivers. So we're
                # only going to track additions here
                if "playersObtained" in team_data:
                    for player_data in team_data["playersObtained"]:
                        pro_player = player_data["proPlayer"]

                        player = self._build_player_from_pro_player(pro_player)

                        trade_detail.add_player(player)

                if "picksObtained" in team_data:
                    for draft_pick in team_data["picksObtained"]:
                        trade_detail.add_draft_pick_with_slot(
                            str(draft_pick["season"]),
                            draft_pick["slot"]["round"],
                            draft_pick["slot"]["slot"])

                trade_details.append(trade_detail)

            all_trades.append(Trade(trade_time, trade_details))

        return all_trades

    def get_weekly_scores_for_league_and_week(
            self,
            league: League,
            week: int,
            year: str = defaults.YEAR) -> List[WeeklyScore]:
        weekly_scores = []
        team_id_to_user = self._league_id_to_team_id_to_user[league.league_id]

        raw_league_scoreboard = api.fetch_league_scoreboard(
            league.league_id, week, year)

        for game in raw_league_scoreboard["games"]:
            raw_home = game["home"]
            raw_away = game["away"]
            home_id = str(raw_home["id"])
            away_id = str(raw_away["id"])

            home_team = Team(
                home_id, team_id_to_user[home_id],
                self._build_roster_link(league.league_id, home_id))
            away_team = Team(
                away_id, team_id_to_user[away_id],
                self._build_roster_link(league.league_id, away_id))

            weekly_scores.append(
                WeeklyScore(league, home_team, week,
                            float(game["homeScore"]["score"]["formatted"])))
            weekly_scores.append(
                WeeklyScore(league, away_team, week,
                            float(game["awayScore"]["score"]["formatted"])))

        return weekly_scores

    def get_season_scores_for_league(self, league: League,
                                     year: str) -> List[SeasonScore]:
        season_scores = []
        team_id_to_user = self._league_id_to_team_id_to_user[league.league_id]

        # The scoreboard returns season-long information regardless of the week
        raw_league_scoreboard = api.fetch_league_scoreboard(
            league.league_id, 1, year)

        for game in raw_league_scoreboard["games"]:
            raw_home = game["home"]
            raw_away = game["away"]
            home_id = str(raw_home["id"])
            away_id = str(raw_away["id"])

            home_team = Team(
                home_id, team_id_to_user[home_id],
                self._build_roster_link(league.league_id, home_id))
            away_team = Team(
                away_id, team_id_to_user[away_id],
                self._build_roster_link(league.league_id, away_id))

            season_scores.append(
                SeasonScore(
                    league, home_team,
                    float(raw_home["pointsFor"]["formatted"].replace(",",
                                                                     ""))))
            season_scores.append(
                SeasonScore(
                    league, away_team,
                    float(raw_away["pointsFor"]["formatted"].replace(",",
                                                                     ""))))

        return season_scores

    def _build_player_from_pro_player(self, player_data: Dict[str,
                                                              str]) -> Player:
        player_id = player_data["id"]
        name = player_data["nameFull"]
        position = player_data["position"]
        team = player_data["proTeamAbbreviation"]

        if "injury" in player_data:
            status = player_data["injury"]["severity"]
        else:
            status = "HEALTHY"

        return Player(player_id, name, team, position, status)

    def _build_roster_link(self, league_id: str, team_id: str) -> str:
        template = "https://www.fleaflicker.com/nfl/leagues/{league_id}/teams/{team_id}"
        return template.format(league_id=league_id, team_id=team_id)

    def _store_team_and_user_data_for_league(self, league_id: str, year: str):
        raw_league_data = api.fetch_league_standings(league_id, year)

        team_id_to_user = {}

        for division in raw_league_data["divisions"]:
            for team in division["teams"]:
                if "owners" in team:
                    user = User(str(team["owners"][0]["id"]),
                                team["owners"][0]["displayName"])
                else:
                    user = User("0", "No user")
                team_id_to_user[str(team["id"])] = user

        self._league_id_to_team_id_to_user[league_id] = team_id_to_user

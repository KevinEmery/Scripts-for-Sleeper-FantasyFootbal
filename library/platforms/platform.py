"""
   Copyright 2022 Kevin Emery

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import re

from typing import Dict, List

from .. import common
from ..model.draftedplayer import DraftedPlayer
from ..model.inactiveroster import InactiveRoster
from ..model.league import League
from ..model.seasonscore import SeasonScore
from ..model.team import Team
from ..model.trade import Trade
from ..model.transaction import Transaction
from ..model.user import User
from ..model.weeklyscore import WeeklyScore


class Platform:
    def get_admin_user_by_identifier(self, identifier: str) -> User:
        pass

    def get_all_leagues_for_user(self,
                                 user: User,
                                 year: str = common.DEFAULT_YEAR,
                                 name_regex: re.Pattern = re.compile(".*"),
                                 store_user_info: bool = True) -> List[League]:
        pass

    def get_drafted_players_for_league(
            self,
            league: League,
            year: str = common.DEFAULT_YEAR) -> List[DraftedPlayer]:
        pass

    def get_all_trades_for_league(self, League: League) -> List[Trade]:
        pass

    def get_weekly_scores_for_league_and_week(self, league: League, week: int,
                                              year: str) -> List[WeeklyScore]:
        pass

    def get_season_scores_for_league(self, league: League,
                                     year: str) -> List[SeasonScore]:
        pass

    def get_last_transaction_for_teams_in_league(
            self, league: League) -> Dict[Team, Transaction]:
        pass

    def get_inactive_rosters_for_league_and_week(
            self,
            league: League,
            week: int,
            player_names_to_ignore: List[str] = []) -> List[InactiveRoster]:
        pass
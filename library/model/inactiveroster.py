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

from typing import List

from .player import Player
from .team import Team
from .transaction import Transaction


class InactiveRoster(object):
    def __init__(self,
                 team: Team,
                 inactive_players: List[Player],
                 last_transaction: Transaction = None):
        self.team = team
        self.inactive_players = inactive_players
        self.last_transaction = last_transaction
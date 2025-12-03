from pydantic import BaseModel
from typing import Literal, Optional, List
from datetime import datetime

# Player models

class Player(BaseModel):
    player_id: str
    name: str
    tag: str
    level: int
    player_card: str
    player_title: str
    region: str
    current_rank: str
    current_rr: int
    current_rank_icon: str
    peak_rank: str
    peak_rank_act: str

class BaseMatchPlayer(BaseModel):
    name: str
    tag: str
    kills: int
    deaths: int

class StandardMatchPlayer(BaseMatchPlayer):
    team: Literal["Red", "Blue"]
    acs: int
    assists: int
    agent: str

class CompMatchPlayer(StandardMatchPlayer):
    rank: str
    rank_icon: str

class FFAMatchPlayer(BaseMatchPlayer):
    score: int

MatchPlayer = StandardMatchPlayer | FFAMatchPlayer

# Match models

class BaseMatch(BaseModel):
    match_id: str
    game_mode: str
    map_name: str
    start_time: datetime
    players: List[MatchPlayer]

class StandardMatch(BaseMatch):
    game_mode: str
    red_score: int
    blue_score: int
    winner: Literal["Red", "Blue"]

class FFAMatch(BaseMatch):
    game_mode: str
    winner: FFAMatchPlayer

Match = StandardMatch | FFAMatch
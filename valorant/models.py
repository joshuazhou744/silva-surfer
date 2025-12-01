from pydantic import BaseModel
from typing import Literal
from datetime import datetime

TeamMode = Literal[
    "competitive",
    "custom", # do sum but this one
    "deathmatch",
    "escalation",
    "teamdeathmatch",
    "newmap",
    "spikerush",
    "swiftplay",
    "replication",
    "snowballfight",
    "unrated",
]

FFAMode = Literal[
    "deathmatch",
]

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


class BaseMatch(BaseModel):
    match_id: str
    game_mode: str
    map_name: str
    start_time: datetime
    players: list[Player]

class TeamMatch(BaseMatch):
    game_mode: TeamMode
    red_score: int
    blue_score: int
    winner: Literal["Red", "Blue"]

class FFAMatch(BaseMatch):
    game_mode: FFAMode
    winner: Player
    top_score: int

class CompMatchPlayer(BaseModel):
    name: str
    tag: str
    team: Literal["Red", "Blue"]
    rank: str
    acs: int
    kills: int
    deaths: int
    assists: int
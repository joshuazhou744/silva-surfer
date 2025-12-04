from pydantic import BaseModel
from typing import List, Union, Optional, Literal
from datetime import datetime
from enum import Enum

# Enums

class GameModeEnum(str, Enum):
    competitive = "competitive"
    custom = "custom"
    deathmatch = "deathmatch"
    escalation = "escalation"
    teamdeathmatch = "teamdeathmatch"
    newmap = "newmap"
    replication = "replication"
    snowballfight = "snowballfight"
    spikerush = "spikerush"
    swiftplay = "swiftplay"
    unrated = "unrated"

# Literals

RankChange = Optional[Literal["rank_up", "rank_down"]]

GameModeLiteral = Literal[
    "competitive",
    "custom",
    "deathmatch",
    "escalation",
    "teamdeathmatch",
    "newmap",
    "replication",
    "snowballfight",
    "spikerush",
    "swiftplay",
    "unrated",
]

# Player/account model

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

# Match player models

class BaseMatchPlayer(BaseModel):
    player_id: str
    name: str
    tag: str
    kills: int
    deaths: int
    agent: str
    agent_id: str
    agent_icon: str
    agent_full: Optional[str] = None

class StandardMatchPlayer(BaseMatchPlayer):
    team: str
    acs: int
    assists: int

class CompMatchPlayer(StandardMatchPlayer):
    rank: str
    rank_icon: str

class FFAMatchPlayer(BaseMatchPlayer):
    score: int

MatchPlayer = Union[StandardMatchPlayer, FFAMatchPlayer, CompMatchPlayer]

# Team models

class StandardTeam(BaseModel):
    team_id: str
    score: int
    players: List[MatchPlayer]

# Match models

class BaseMatch(BaseModel):
    match_id: str
    game_mode: str
    map_name: str
    map_banner: str
    start_time: datetime

class StandardMatch(BaseMatch):
    red_score: int
    blue_score: int
    teams: List[StandardTeam]
    winner: StandardTeam | None

class FFAMatch(BaseMatch):
    players: List[FFAMatchPlayer]
    winner: FFAMatchPlayer | None

Match = Union[StandardMatch, FFAMatch]

# Target player model

class TargetPlayer(BaseModel):
    player: MatchPlayer
    won: bool
    agent_full: str
    rr_change: Optional[int] = None
    rank_change: RankChange

# Player Match view

class PlayerMatchView(BaseModel):
    match: Match
    target_player: TargetPlayer
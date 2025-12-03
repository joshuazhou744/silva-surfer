from typing import List
from datetime import datetime
from models import (
    Match,
    StandardMatch,
    FFAMatch,
    StandardMatchPlayer,
    CompMatchPlayer,
    FFAMatchPlayer,
)
from config import BASE_URL, VALORANT_PLATFORM, VALORANT_RANK_ICON_URL, SESSION, get_account_data


def calc_acs(score: int, total_rounds: int) -> int:
    if total_rounds == 0:
        return 0
    return round(score / total_rounds)

def parse_standard_player(player: dict, total_rounds: int, is_comp: bool):
    stats = player["stats"]

    acs = calc_acs(stats["score"], total_rounds)

    base_kwargs = dict(
        name=player["name"],
        tag=player["tag"],
        kills=stats["kills"],
        deaths=stats["deaths"],
        assists=stats["assists"],
        team=player["team_id"],
        acs=acs,
    )

    if is_comp:
        tier = player["tier"]

        return CompMatchPlayer(
            **base_kwargs,
            rank=tier["name"],
            rank_icon=f"{VALORANT_RANK_ICON_URL}/{tier['id']}/smallicon.png",
        )

    return StandardMatchPlayer(**base_kwargs)

def parse_ffa_player(player: dict):
    stats = player["stats"]

    return FFAMatchPlayer(
        name=player["name"],
        tag=player["tag"],
        kills=stats["kills"],
        deaths=stats["deaths"],
        score=stats["score"],
    )

def get_match_history(username: str, tag: str, size: int = 5, mode: str = None) -> List[Match]:
    # get region with the helper function
    account_data = get_account_data(username, tag)
    region = account_data["region"]

    url = f"{BASE_URL}/v4/matches/{region}/{VALORANT_PLATFORM}/{username}/{tag}"

    params = {
        "size": size,
        "mode": mode,
    }

    response = SESSION.get(url, params=params)

    if response.status_code == 404:
        raise ValueError(f"No matches found for '{username}#{tag}'")

    if response.status_code != 200:
        raise RuntimeError(
            f"Match history API failed: {response.status_code} {response.text}"
        )

    matches: List[Match] = []
    matches_raw = response.json()["data"]

    for match_data in matches_raw:
        metadata = match_data["metadata"]
        queue = metadata["queue"]

        match_id = metadata["match_id"]
        game_mode = queue["name"]
        map_name = metadata["map"]["name"]
        start_time = datetime.fromisoformat(metadata["started_at"].replace("Z", "+00:00"))

        teams = match_data.get("teams", [])
        players_raw = match_data["players"]

        # Not standard match, likely Deathmatch
        if queue["mode_type"] != "Standard":
            ffa_players: List[FFAMatchPlayer] = [
                parse_ffa_player(p)
                for p in players_raw
            ]

            winner = max(ffa_players, key=lambda p: p.score)

            ffa_match = FFAMatch(
                match_id=match_id,
                game_mode=game_mode,
                map_name=map_name,
                start_time=start_time,
                players=ffa_players,
                winner=winner,
            )

            matches.append(ffa_match)
            continue

        # Standard match, 5v5 team based
        total_rounds = sum(
            team["rounds"]["won"] + team["rounds"]["lost"]
            for team in teams
        ) // 2

        # find winning team
        winner = next(
            team["team_id"]
            for team in teams
            if team["won"]
        )

        red_score = next(
            t["rounds"]["won"] for t in teams if t["team_id"] == "Red"
        )

        blue_score = next(
            t["rounds"]["won"] for t in teams if t["team_id"] == "Blue"
        )

        is_competitive = queue["id"] == "competitive"

        players = [
            parse_standard_player(
                p,
                total_rounds=total_rounds,
                is_comp=is_competitive,
            )
            for p in players_raw
        ]

        team_match = StandardMatch(
            match_id=match_id,
            game_mode=game_mode,
            map_name=map_name,
            start_time=start_time,
            players=players,
            red_score=red_score,
            blue_score=blue_score,
            winner=winner,
        )

        matches.append(team_match)

    return matches


region = "na"
name = "Candice"
tag = "9982"

url = f"{BASE_URL}/v4/matches/{region}/{VALORANT_PLATFORM}/{name}/{tag}"

params = {
    "size": 1,
    "mode": "deathmatch",
}

response = SESSION.get(url, params=params)
data = response.json()["data"][0]

from pprint import pprint
pprint(data["players"])
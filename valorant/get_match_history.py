from typing import List, Optional
from datetime import datetime
from .models import (
    Match,
    StandardMatch,
    FFAMatch,
    StandardMatchPlayer,
    CompMatchPlayer,
    FFAMatchPlayer,
    StandardTeam,
    PlayerMatchView,
    TargetPlayer,
    RankChange,
)
from .services import (
    get_account_data,
    get_agent_icon_url,
    get_rank_icon_url,
    get_matchlist_data,
    get_map_banner_url,
    get_full_agent_url,
    get_mmr_history_data,
)

MAX_MATCHES = 5

def calc_acs(score: int, total_rounds: int) -> int:
    if total_rounds == 0:
        return 0
    return round(score / total_rounds)

def parse_base_player(player: dict) -> dict:
    return {
        "player_id": player["puuid"],
        "name": player["name"],
        "tag": player["tag"],
        "kills": player["stats"]["kills"],
        "deaths": player["stats"]["deaths"],
        "agent": player["agent"]["name"],
        "agent_id": player["agent"]["id"],
        "agent_icon": get_agent_icon_url(player["agent"]["id"]),
    }

def parse_standard_player(player: dict, total_rounds: int, is_comp: bool) -> StandardMatchPlayer | CompMatchPlayer:
    base_player_kwargs = parse_base_player(player)
    acs = calc_acs(player["stats"]["score"], total_rounds)

    base_standard_kwargs = dict(
        **base_player_kwargs,
        assists=player["stats"]["assists"],
        acs=acs,
        team=player["team_id"],
    )

    if is_comp:
        tier = player["tier"]

        return CompMatchPlayer(
            **base_standard_kwargs,
            rank=tier["name"],
            rank_icon=get_rank_icon_url(tier["id"]),
        )

    return StandardMatchPlayer(**base_standard_kwargs)

def parse_ffa_player(player: dict) -> FFAMatchPlayer:
    base_player_kwargs = parse_base_player(player)

    return FFAMatchPlayer(
        **base_player_kwargs,
        score=player["stats"]["score"],
    )

def get_base_match_data(match_data: dict) -> tuple[dict, list[dict]]:
    metadata = match_data["metadata"]
    queue = metadata["queue"]
    map = metadata["map"]

    match_id = metadata["match_id"]
    game_mode = queue["name"]
    map_name = map["name"]
    map_banner = get_map_banner_url(map["id"])
    start_time = datetime.fromisoformat(metadata["started_at"].replace("Z", "+00:00")).astimezone()

    players_raw = match_data["players"]

    base_match_dict = dict(
        match_id=match_id,
        game_mode=game_mode,
        map_name=map_name,
        map_banner=map_banner,
        start_time=start_time,
    )

    return base_match_dict, players_raw

def get_standard_teams(teams_data: list[dict], players_data: list[dict], is_comp: bool) -> tuple[StandardTeam, StandardTeam]:
    blue_team_dict = next((team for team in teams_data if team["team_id"] == "Blue"), None)
    red_team_dict = next((team for team in teams_data if team["team_id"] == "Red"), None)

    if not blue_team_dict or not red_team_dict:
        raise ValueError("Invalid team data: missing blue or red team")
    
    rounds_played = blue_team_dict["rounds"]["won"] + blue_team_dict["rounds"]["lost"]
    
    blue_players_dict = [p for p in players_data if p["team_id"] == blue_team_dict["team_id"]]
    red_players_dict = [p for p in players_data if p["team_id"] == red_team_dict["team_id"]]

    blue_players = [parse_standard_player(p, rounds_played, is_comp=is_comp) for p in blue_players_dict]
    red_players = [parse_standard_player(p, rounds_played, is_comp=is_comp) for p in red_players_dict]
    
    blue_team = StandardTeam(
        team_id=blue_team_dict["team_id"],
        score=blue_team_dict["rounds"]["won"],
        players=blue_players,
    )

    red_team = StandardTeam(
        team_id=red_team_dict["team_id"],
        score=red_team_dict["rounds"]["won"],
        players=red_players,
    )

    return blue_team, red_team

def get_ffa_match(match_data: dict) -> FFAMatch:
    base_match_kwargs, players_raw = get_base_match_data(match_data)

    ffa_players = [parse_ffa_player(p) for p in players_raw]

    winner = max(ffa_players, key=lambda p: p.score) if ffa_players else None

    return FFAMatch(
        **base_match_kwargs,
        players=ffa_players,
        winner=winner,
    )

def get_standard_match(match_data: dict, is_comp: bool) -> StandardMatch:
    base_match_kwargs, players_raw = get_base_match_data(match_data)
    blue_team, red_team = get_standard_teams(match_data["teams"], players_raw, is_comp=is_comp)
    if blue_team.score == red_team.score:
        winner = None
    elif blue_team.score > red_team.score:
        winner = blue_team
    else:
        winner = red_team

    standard_match_kwargs = dict(
        **base_match_kwargs,
        red_score=red_team.score,
        blue_score=blue_team.score,
        teams=[blue_team, red_team],
        winner=winner,
    )

    return StandardMatch(**standard_match_kwargs)


def get_mmr_history(region: str, puuid: str):
    mmr_data = get_mmr_history_data(region, puuid)
    mmr_by_match_id = {
        h["match_id"]: h for h in mmr_data.get("history", [])
    }
    return mmr_by_match_id

def get_target_comp_values(mmr_data_map: dict[str, dict], match_id: str) -> tuple[Optional[int], RankChange]:
    if match_id not in mmr_data_map:
        return None, None

    mmr_data = mmr_data_map[match_id]
    rr_change = mmr_data["last_change"]

    rank_change = detect_rank_change(mmr_data)

    return rr_change, rank_change

def detect_rank_change(mmr: dict) -> RankChange:
    rr = mmr["rr"]
    delta = mmr["last_change"]
    protected = mmr["was_derank_protected"]
    pre_rr = (100 + rr - delta) % 100

    # rank protection, no rank change
    if protected:
        return None

    # Rank up
    if delta > 0 and (pre_rr + delta >= 100 or delta >= rr):
        return "rank_up"

    # Rank down
    if delta < 0 and rr - delta == 100:
        return "rank_down"

    return None

def build_player_view(match: Match, target_puuid: str, mmr_data_map: dict[str, dict]) -> PlayerMatchView | None:
    if isinstance(match, StandardMatch):
        for team in match.teams:
            for player in team.players:
                if player.player_id == target_puuid:
                    rr_change, rank_change = get_target_comp_values(mmr_data_map, match.match_id)
                    target_player = TargetPlayer(
                        player=player,
                        won=(team == match.winner),
                        agent_full=get_full_agent_url(player.agent_id),
                        rr_change=rr_change,
                        rank_change=rank_change,
                    )
                    return PlayerMatchView(match=match, target_player=target_player)
    elif isinstance(match, FFAMatch):
        for player in match.players:
            if player.player_id == target_puuid:
                target_player = TargetPlayer(
                    player=player,
                    won=(match.winner and target_puuid == match.winner.player_id),
                    agent_full=get_full_agent_url(player.agent_id),
                )
                return PlayerMatchView(match=match, target_player=target_player)


def get_match_history(username: str, tag: str, size: int = 1, mode: str | None = None) -> List[PlayerMatchView]:
    size = min(size, MAX_MATCHES)

    # get region and player id with the helper function
    account_data = get_account_data(username, tag)
    region = account_data["region"]
    puuid = account_data["puuid"]

    matches_raw = get_matchlist_data(region, username, tag, size=size, mode=mode)

    mmr_data_map = get_mmr_history(region, puuid)

    views: List[PlayerMatchView] = []

    for match_data in matches_raw:
        metadata = match_data["metadata"]
        queue = metadata["queue"]

        if queue["mode_type"] == "Deathmatch":
            # Not standard match, likely Deathmatch
            match = get_ffa_match(match_data)
        else:
            # Else: standard match, 5v5 team based
            is_comp = queue["name"] == "Competitive"
            match = get_standard_match(match_data=match_data, is_comp=is_comp)

        view = build_player_view(match, puuid, mmr_data_map)

        if view:
            views.append(view)

    # print(views)
    return views

# region = "na"
# name = "stickeylickey"
# tag = "stink"
# mode = "competitive"
# size = 5

# matches = get_match_history(name, tag, size=size, mode=mode)
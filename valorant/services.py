import requests
from .config import (
    BASE_URL,
    SESSION,
    VALORANT_PLATFORM,
    VALORANT_RANK_ICON_URL,
    VALORANT_CARD_URL,
    VALORANT_TITLE_URL,
    VALORANT_AGENT_URL,
    VALORANT_MAP_URL,
)

def get_account_data(username: str, tag: str) -> str:
    account_url = f"{BASE_URL}/v2/account/{username}/{tag}"
    account_response = SESSION.get(account_url)

    if account_response.status_code == 404:
        raise ValueError(f"Account '{username}#{tag}' not found")

    if account_response.status_code != 200:
        raise RuntimeError(
            f"Account API request failed: {account_response.status_code} {account_response.text}"
        )
    
    account_data = account_response.json()["data"]
    return account_data

def get_mmr_data(region: str, username: str, tag: str, platform: str = VALORANT_PLATFORM) -> dict:
    mmr_url = f"{BASE_URL}/v3/mmr/{region}/{platform}/{username}/{tag}"
    mmr_response = SESSION.get(mmr_url)

    if mmr_response.status_code != 200:
        raise RuntimeError(
            f"MMR API request failed: {mmr_response.status_code} {mmr_response.text}"
        )
    
    return mmr_response.json()["data"]

def get_matchlist_data(region: str, username: str, tag: str, size: int, mode: str | None = None, platform: str = VALORANT_PLATFORM) -> dict:
    url = f"{BASE_URL}/v4/matches/{region}/{platform}/{username}/{tag}"

    params = {
        "size": size,
    }
    if mode:
        params["mode"] = mode

    response = SESSION.get(url, params=params)

    if response.status_code == 404:
        raise ValueError(f"No matches found for '{username}#{tag}'")

    if response.status_code != 200:
        raise RuntimeError(
            f"Match history API failed: {response.status_code} {response.text}"
        )
    
    return response.json()["data"]

def get_mmr_history_data(region: str, puuid: str, platform: str = VALORANT_PLATFORM) -> dict:
    mmr_history_url = f"{BASE_URL}/v2/by-puuid/mmr-history/{region}/{platform}/{puuid}"
    mmr_history_response = SESSION.get(mmr_history_url)

    if mmr_history_response.status_code != 200:
        raise RuntimeError(
            f"MMR API request failed: {mmr_history_response.status_code} {mmr_history_response.text}"
        )
    
    return mmr_history_response.json()["data"]

def get_player_title(title_id: str) -> str:
    title_url = f"{VALORANT_TITLE_URL}/{title_id}"
    title_response = requests.get(title_url)

    if title_response.status_code != 200:
        raise RuntimeError(
            f"Title API request failed: {title_response.status_code} {title_response.text}"
        )
    
    title_text = title_response.json()["data"]["titleText"] or ""
    return title_text

def get_agent_icon_url(agent_id: str) -> str:
    return f"{VALORANT_AGENT_URL}/{agent_id}/displayicon.png"

def get_full_agent_url(agent_id: str) -> str:
    return f"{VALORANT_AGENT_URL}/{agent_id}/fullportrait.png"

def get_player_card_url(card_id: str) -> str:
    return f"{VALORANT_CARD_URL}/{card_id}/wideart.png"

def get_rank_icon_url(rank_id: str) -> str:
    return f"{VALORANT_RANK_ICON_URL}/{rank_id}/smallicon.png"

def get_map_banner_url(map_id: str) -> str:
    return f"{VALORANT_MAP_URL}/{map_id}/listviewicon.png"
from .models import Player
from .config import BASE_URL, VALORANT_PLATFORM, VALORANT_RANK_ICON_URL, VALORANT_CARD_URL, VALORANT_TITLE_URL, SESSION
import requests

# USERNAME = "stickeylickey"
# TAG = "stink"

def get_player(username: str, tag: str) -> Player:
    account_url = f"{BASE_URL}/v2/account/{username}/{tag}"
    account_response = SESSION.get(account_url)

    if account_response.status_code == 404:
        raise ValueError(f"Account '{username}#{tag}' not found")
    
    if account_response.status_code != 200:
        raise RuntimeError(
            f"Account API request failed: {account_response.status_code} {account_response.text}"
        )
    
    account_data = account_response.json()["data"]
    # get region so we can get mmr
    region = account_data["region"]
    
    mmr_url = f"{BASE_URL}/v3/mmr/{region}/{VALORANT_PLATFORM}/{username}/{tag}"
    mmr_response = SESSION.get(mmr_url)

    if mmr_response.status_code != 200:
        raise RuntimeError(
            f"MMR API request failed: {mmr_response.status_code} {mmr_response.text}"
        )
    
    mmr_data = mmr_response.json()["data"]

    # get title
    title_id = account_data["title"]
    title_url = f"{VALORANT_TITLE_URL}/{title_id}"
    title_response = requests.get(title_url).json()

    title_text = title_response["data"]["titleText"] or ""

    # build player object
    player = Player(
        player_id=account_data["puuid"],
        name=account_data["name"],
        tag=account_data["tag"],
        level=account_data["account_level"],
        player_card=f"{VALORANT_CARD_URL}/{account_data['card']}/wideart.png",
        player_title=title_text,
        region=region,
        current_rank=mmr_data["current"]["tier"]["name"],
        current_rr=mmr_data["current"]["rr"],
        current_rank_icon=f"{VALORANT_RANK_ICON_URL}/{mmr_data['current']['tier']['id']}/smallicon.png",
        peak_rank=mmr_data["peak"]["tier"]["name"],
        peak_rank_act=mmr_data["peak"]["season"]["short"],
    )
    # print(player)
    return player

# try:
#     get_player(USERNAME, TAG)
# except Exception as e:
#     print("error", e)
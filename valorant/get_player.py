from .models import Player
from .services import get_account_data, get_player_card_url, get_player_title, get_rank_icon_url, get_mmr_data

def get_player(username: str, tag: str) -> Player:
    account_data = get_account_data(username, tag)
    region = account_data["region"]
    
    mmr_data = get_mmr_data(region, username, tag)

    # build player object
    player = Player(
        player_id=account_data["puuid"],
        name=account_data["name"],
        tag=account_data["tag"],
        level=account_data["account_level"],
        player_card=get_player_card_url(account_data["card"]),
        player_title=get_player_title(account_data["title"]),
        region=region,
        current_rank=mmr_data["current"]["tier"]["name"],
        current_rr=mmr_data["current"]["rr"],
        current_rank_icon=get_rank_icon_url(mmr_data["current"]["tier"]["id"]),
        peak_rank=mmr_data["peak"]["tier"]["name"],
        peak_rank_act=mmr_data["peak"]["season"]["short"],
    )
    # print(player)
    return player


# USERNAME = "darumaka"
# TAG = "zenn"
# try:
#     print(get_player(USERNAME, TAG))
# except Exception as e:
#     print("error", e)
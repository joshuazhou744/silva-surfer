from dotenv import load_dotenv
import os
import requests

load_dotenv()

VALORANT_API_KEY = os.getenv("VALORANT_API_KEY")
DEFAULT_VALORANT_REGION = os.getenv("VALORANT_REGION", "na")
VALORANT_PLATFORM = os.getenv("VALORANT_PLATFORM", "pc")
BASE_URL = os.getenv("VALORANT_BASE_URL", "https://api.henrikdev.xyz/valorant")
VALORANT_RANK_ICON_URL = os.getenv("VALORANT_RANK_ICON_URL", "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04")
VALORANT_CARD_URL = os.getenv("VALORANT_CARD_URL", "https://media.valorant-api.com/playercards")
VALORANT_TITLE_URL = os.getenv("VALORANT_TITLE_URL", "https://valorant-api.com/v1/playertitles")

if not VALORANT_API_KEY:
    raise RuntimeError("VALORANT_API_KEY not set")


HEADERS = {
    "Authorization": VALORANT_API_KEY,
    "Accept": "*/*",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

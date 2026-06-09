from dotenv import load_dotenv
import os

load_dotenv()

BOT_API_TOKEN = os.getenv('BOT_API_TOKEN')
CHANNEL_BOT_ID = os.getenv('CHANNEL_BOT_ID')
BASE_URL = os.getenv('BASE_URL')
BACKEND_URL = os.getenv('BACKEND_URL')
VIBIX_PUBLISHER_ID = os.getenv('VIBIX_PUBLISHER_ID', '678153547')
TMDB_READ_TOKEN = os.getenv("TMDB_READ_TOKEN")
TMDB_API_BASE = os.getenv("TMDB_API_BASE", "https://api.themoviedb.org/3")
ADMIN_IDS = {
    int(user_id)
    for user_id in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",")
    if user_id
}

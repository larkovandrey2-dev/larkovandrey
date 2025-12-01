from dotenv import load_dotenv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "helpers", "models", "linear_reg")

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

ADMINS_STR = os.getenv('ADMINS', '')
ADMINS = list(map(int, ADMINS_STR.split(','))) if ADMINS_STR else []
API_URL = os.getenv('API_URL', 'http://localhost:8000/api')


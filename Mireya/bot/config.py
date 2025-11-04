import os

from dotenv import load_dotenv
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "linear_reg")
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMINS = list(map(int,os.getenv('ADMINS').split(',')))

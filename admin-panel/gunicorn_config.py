import os
from dotenv import load_dotenv

load_dotenv()

APP_HOST = os.environ.get("APP_HOST")
APP_PORT = os.environ.get("APP_PORT")

bind = f"{APP_HOST}:{APP_PORT}"

import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_APPLICATION_ACCESS_KEY = os.getenv("GOOGLE_APPLICATION_ACCESS_KEY")
GOOGLE_APP_ID = os.getenv("GOOGLE_APP_ID")
GOOGLE_APP_SCRIPT_ID = os.getenv("GOOGLE_APP_SCRIPT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHROME_PROFILE_PATH = r"C:\chrome-selenium-profile"
GOOGLE_APP_SCRIPT_URL = os.getenv("GOOGLE_APP_SCRIPT_URL")
LOG_DIRECTORY= os.getenv("LOG_DIRECTORY")
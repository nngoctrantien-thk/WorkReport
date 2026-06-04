import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_APPLICATION_ACCESS_KEY = os.getenv("GOOGLE_APPLICATION_ACCESS_KEY")
GOOGLE_APP_ID = os.getenv("GOOGLE_APP_ID")
GOOGLE_APP_SCRIPT_ID = os.getenv("GOOGLE_APP_SCRIPT_ID")
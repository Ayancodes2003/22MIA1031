import os
from dotenv import load_dotenv

load_dotenv()

def get_access_token():
    return os.getenv("ACCESS_TOKEN")

import os

from dotenv import load_dotenv

load_dotenv()

class Settings:
    BASE_URL = os.getenv("BASE_URL")
    API_BASE_URL = os.getenv("API_BASE_URL")

    USERNAME = os.getenv("USERNAME")
    PASSWORD = os.getenv("PASSWORD")
    MFA_SECRET = os.getenv("MFA_SECRET")

    HEADLESS = os.getenv("HEADLESS")


settings = Settings()

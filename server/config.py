import os

from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    if os.environ.get("ENV") == "test":
        return os.environ.get("DATABASE_URL_TEST")
    else:
        return os.environ.get("DATABASE_URL")

ACCESS_KEY: str | None = os.environ.get("ACCESS_KEY")
SECRET_KEY: str | None = os.environ.get("SECRET_KEY")
ENDPOINT_URL: str | None = os.environ.get("ENDPOINT_URL")
BUCKET_NAME: str | None = os.environ.get("BUCKET_NAME")
WEB_URL: str | None = os.environ.get("WEB_URL")

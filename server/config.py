import os

from dotenv import load_dotenv

load_dotenv()


DB_USER: str | None = os.environ.get("DB_USER")
DB_PASS: str | None = os.environ.get("DB_PASS")
DB_HOST: str | None = os.environ.get("DB_HOST")
DB_PORT: str | None = os.environ.get("DB_PORT")
DB_NAME: str | None = os.environ.get("DB_NAME")


ACCESS_KEY: str | None = os.environ.get("ACCESS_KEY")
SECRET_KEY: str | None = os.environ.get("SECRET_KEY")
ENDPOINT_URL: str | None = os.environ.get("ENDPOINT_URL")
BUCKET_NAME: str | None = os.environ.get("BUCKET_NAME")
WEB_URL: str | None = os.environ.get("WEB_URL")

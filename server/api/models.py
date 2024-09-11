from contextlib import asynccontextmanager
from datetime import datetime

from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ARRAY,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, backref

from server.database.db_connection import Base


class Tweet(Base):
    __tablename__ = "tweets"
    id = Column(Integer, autoincrement=True, primary_key=True)
    content = Column(Text)
    attachment = Column(ARRAY(String))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref=backref("tweets", lazy=True))


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, autoincrement=True, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    api_key = Column(String, unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tweet_id = Column(Integer, ForeignKey("tweets.id"), nullable=False)

    user = relationship("User", backref=backref("likes", lazy=True))
    tweet = relationship("Tweet", backref=backref("likes", lazy=True))


class Follow(Base):
    __tablename__ = "followers"

    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship(
        "User", foreign_keys=[user_id], backref=backref("following", lazy=True)
    )
    follower = relationship(
        "User", foreign_keys=[follower_id], backref=backref("followers", lazy=True)
    )

    __table_args__ = (UniqueConstraint("user_id", "follower_id", name="unique_follow"),)


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, autoincrement=True, primary_key=True)
    file_link = Column(String)
    tweet_id = Column(Integer, ForeignKey("tweets.id"))

    tweet = relationship("Tweet", backref=backref("media_files", lazy=True))


class S3Client:
    def __init__(
            self,
            access_key: str,
            secret_key: str,
            endpoint_url: str,
            bucket_name: str,
            web_url: str,
    ):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
        }
        self.bucket_name = bucket_name
        self.web_url = web_url
        self.session = get_session()

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config, verify=False) as client:
            yield client

    async def upload_file_obj(self, file_obj, object_name: str):
        try:
            async with self.get_client() as client:
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=file_obj,
                )
        except ClientError as e:
            print(f"Error uploading file: {e}")

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
    """
    Model representing tweets in the system.

    Attributes:
        id (int): Unique identifier for the tweet.
        content (str): The textual content of the tweet.
        attachment (ARRAY[str]): An array of strings, storing media file links.
        user_id (int): Foreign key referring to the user who created the tweet.
        created_at (datetime): The timestamp when the tweet was created, defaults to current time.
    """

    __tablename__ = "tweets"
    id = Column(Integer, autoincrement=True, primary_key=True)
    content = Column(Text)
    attachment = Column(ARRAY(String))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref=backref("tweets", lazy=True))


class User(Base):
    """
    Model representing users in the system.

    Attributes:
        id (int): Unique identifier for the user.
        username (str): Username (unique).
        api_key (str): API key for authentication.
        name (str): Real name of the user.
        email (str): Email address of the user (unique).
        created_at (datetime): Timestamp when the user was created.
    """

    __tablename__ = "users"
    id = Column(Integer, autoincrement=True, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    api_key = Column(String, unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Like(Base):
    """
    Model representing likes made by users on tweets.

    Attributes:
        id (int): Unique identifier for the like.
        user_id (int): Foreign key referring to the user who liked the tweet.
        tweet_id (int): Foreign key referring to the liked tweet.
    """

    __tablename__ = "likes"

    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tweet_id = Column(Integer, ForeignKey("tweets.id"), nullable=False)

    user = relationship("User", backref=backref("likes", lazy=True))
    tweet = relationship("Tweet", backref=backref("likes", lazy=True))


class Follow(Base):
    """
    Model representing follow relationships between users.

    Attributes:
        id (int): Unique identifier for the follow relationship.
        user_id (int): Foreign key referring to the user who is following.
        follower_id (int): Foreign key referring to the user being followed.
    """

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
    """
    Model representing media files attached to tweets.

    Attributes:
        id (int): Unique identifier for the media file.
        file_link (str): Link to the media file stored in S3.
        tweet_id (int): Foreign key referring to the tweet the media is attached to.
    """

    __tablename__ = "media"

    id = Column(Integer, autoincrement=True, primary_key=True)
    file_link = Column(String)
    tweet_id = Column(Integer, ForeignKey("tweets.id"))

    tweet = relationship("Tweet", backref=backref("media_files", lazy=True))


class S3Client:
    """
    Class for interacting with S3-compatible storage.

    Params:
        access_key (str): Access key for authentication.
        secret_key (str): Secret key for authentication.
        endpoint_url (str): URL of the S3-compatible storage.
        bucket_name (str): Name of the S3 bucket where files are uploaded.
        web_url (str): Base URL for accessing files via HTTP.

    Methods:
        get_client(): Returns an S3 client for interacting with storage.
        upload_file_obj(file_obj, object_name): Asynchronously uploads a file to S3.
    """

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
        """
        Asynchronous context manager for obtaining an S3 client.
        """
        async with self.session.create_client(
            "s3", **self.config, verify=False
        ) as client:
            yield client

    async def upload_file_obj(self, file_obj, object_name: str):
        """
        Asynchronously uploads a file object to S3.

        Params:
            file_obj: The file object to upload.
            object_name (str): The name of the file in the bucket.
        """
        try:
            async with self.get_client() as client:
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=file_obj,
                )
        except ClientError as e:
            print(f"Error uploading file: {e}")

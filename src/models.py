from datetime import datetime

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

from database import Base


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

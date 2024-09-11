from typing import List, Optional

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    name: str

class UserResponse(BaseModel):
    result: bool
    user: UserOut
    followers: List[UserOut]
    followings: List[UserOut]

class Like(BaseModel):
    user_id: int
    name: str


class BaseTweet(BaseModel):
    content: str = Field(..., title="tweet text")


class TweetIn(BaseTweet):
    content: str = Field(..., alias="tweet_data")
    tweet_media_ids: Optional[List[int]] = None


class TweetOut(BaseTweet):
    id: int
    attachments: List[str] = Field(default=[], title="List of attachments")
    user: UserOut
    likes: List[Like] = []


class TweetResponse(BaseModel):
    result: bool
    tweets: List[TweetOut]


class MediaResponse(BaseModel):
    result: bool
    media_id: Optional[int]

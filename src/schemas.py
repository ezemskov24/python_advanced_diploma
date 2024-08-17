from typing import List

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
    content: str = Field(..., title="Tweet text")


class TweetIn(BaseTweet):
    attachment: List[str] = Field(default=[], title="List of attachments")


class TweetOut(BaseTweet):
    id: int
    attachments: List[str] = Field(default=[], title="List of attachments")
    user: UserOut
    likes: List[Like] = []


class TweetResponse(BaseModel):
    result: bool
    tweets: List[TweetOut]

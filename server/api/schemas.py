from typing import List, Optional

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    """
    Model representing a user in response.

    Attributes:
        id (int): Unique identifier of the user.
        name (str): Name of the user.
    """

    id: int
    name: str


class UserResponse(BaseModel):
    """
    Model representing a response containing user information and their followers and followings.

    Attributes:
        result (bool): Status of the response.
        user (UserOut): Information about the user.
        followers (List[UserOut]): List of followers for the user.
        followings (List[UserOut]): List of users that the user is following.
    """

    result: bool
    user: UserOut
    followers: List[UserOut]
    followings: List[UserOut]


class Like(BaseModel):
    """
    Model representing a like given by a user.

    Attributes:
        user_id (int): Unique identifier of the user who liked the tweet.
        name (str): Name of the user who liked the tweet.
    """

    user_id: int
    name: str


class BaseTweet(BaseModel):
    """
    Base model for tweet data.

    Attributes:
        content (str): Text content of the tweet.
    """

    content: str = Field(..., title="tweet text")


class TweetIn(BaseTweet):
    """
    Model for incoming tweet data.

    Attributes:
        content (str): Text content of the tweet, with an alias 'tweet_data' for incoming data.
        tweet_media_ids (Optional[List[int]]): List of media IDs associated with the tweet.
    """

    content: str = Field(..., alias="tweet_data")
    tweet_media_ids: Optional[List[int]] = None


class TweetOut(BaseTweet):
    """
    Model representing a tweet in response.

    Attributes:
        id (int): Unique identifier of the tweet.
        attachments (List[str]): List of links to attachments associated with the tweet.
        user (UserOut): Information about the user who created the tweet.
        likes (List[Like]): List of likes for the tweet.
    """

    id: int
    attachments: List[str] = Field(default=[], title="List of attachments")
    user: UserOut
    likes: List[Like] = []


class TweetResponse(BaseModel):
    """
    Model representing a response containing a list of tweets.

    Attributes:
        result (bool): Status of the response.
        tweets (List[TweetOut]): List of tweets.
    """

    result: bool
    tweets: List[TweetOut]

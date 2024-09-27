from datetime import datetime

import pytest
from unittest.mock import patch
from io import BytesIO

from sqlalchemy import select

from server.api.routers import s3_client
from server.api.models import Media, Tweet, User, Follow, Like
from tests.conftest import db_session


@pytest.mark.asyncio
async def test_create_new_tweet(test_user, client):
    """
    Test of creating a new tweet
    """
    content = {"tweet_data": "This is a test tweet", "tweet_media_ids": []}
    response = await client.post(
        "/api/tweets", json=content, headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_upload_media(client, db_session):
    """
    Test of upload media to S3
    """
    with patch("server.api.routers.s3_client.upload_file_obj") as mock_upload:
        mock_upload.return_value = None

        test_file = BytesIO(b"Test file content")
        test_file.name = "test_image.jpg"

        response = await client.post(
            "/api/medias", files={"file": ("test_image.jpg", test_file, "image/jpeg")}
        )

        assert response.status_code == 200, response.text

        json_response = response.json()
        assert json_response["result"] is True
        assert "media_id" in json_response

        media_record = await db_session.execute(
            select(Media).where(Media.id == json_response["media_id"])
        )
        media = media_record.scalar_one_or_none()
        assert media is not None
        assert media.file_link.startswith(
            f"{s3_client.web_url}/{s3_client.bucket_name}/"
        )


@pytest.mark.asyncio
async def test_delete_own_tweet(client, test_user, db_session):
    """
    Test of delete own tweet
    """
    tweet = Tweet(content="This is a test tweet", user_id=test_user.id)
    db_session.add(tweet)
    await db_session.commit()
    await db_session.refresh(tweet)

    response = await client.delete(
        f"/api/tweets/{tweet.id}", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 200, response.text

    json_response = response.json()
    assert json_response["result"] is True

    deleted_tweet = await db_session.execute(select(Tweet).where(Tweet.id == tweet.id))
    assert deleted_tweet.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_other_user_tweet(client, test_user, db_session):
    """
    Test of deleting someone else's tweet
    """
    other_user = User(
        username="otheruser",
        api_key="otherapikey",
        name="Other User",
        email="otheruser@example.com",
        created_at=datetime.utcnow(),
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    other_user_tweet = Tweet(
        content="This is someone else's tweet", user_id=other_user.id
    )
    db_session.add(other_user_tweet)
    await db_session.commit()
    await db_session.refresh(other_user_tweet)

    response = await client.delete(
        f"/api/tweets/{other_user_tweet.id}", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 403, response.text

    json_response = response.json()
    assert json_response["detail"] == "You can only delete your own tweets"


@pytest.mark.asyncio
async def test_delete_nonexistent_tweet(client, test_user):
    """
    Test of deleting a non-existent tweet
    """
    response = await client.delete(
        "/api/tweets/9999", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_follow_user(client, test_user, db_session):
    """
    Test of creating a subscription to a user
    """
    follow_user = User(
        username="followuser",
        api_key="followapikey",
        name="Follow User",
        email="followuser@example.com",
        created_at=datetime.utcnow(),
    )
    db_session.add(follow_user)
    await db_session.commit()
    await db_session.refresh(follow_user)

    response = await client.post(
        f"/api/users/{follow_user.id}/follow", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 200, response.text

    json_response = response.json()
    assert json_response["result"] is True

    follow_record = await db_session.execute(
        select(Follow).where(
            Follow.user_id == test_user.id, Follow.follower_id == follow_user.id
        )
    )
    assert follow_record.scalars().first() is not None


@pytest.mark.asyncio
async def test_follow_self(client, test_user):
    """
    Test of follow to yourself
    """
    response = await client.post(
        f"/api/users/{test_user.id}/follow", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 400, response.text

    json_response = response.json()
    assert json_response["detail"] == "You cannot follow yourself"


@pytest.mark.asyncio
async def test_follow_already_following(client, test_user, db_session):
    """
    Test of follow to a user who is already subscribed to
    """
    follow_user = User(
        username="followuser",
        api_key="followapikey",
        name="Follow User",
        email="followuser@example.com",
        created_at=datetime.utcnow(),
    )
    db_session.add(follow_user)
    await db_session.commit()
    await db_session.refresh(follow_user)

    new_follow = Follow(user_id=test_user.id, follower_id=follow_user.id)
    db_session.add(new_follow)
    await db_session.commit()

    response = await client.post(
        f"/api/users/{follow_user.id}/follow", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 400, response.text

    json_response = response.json()
    assert json_response["detail"] == "You are already following this user"


@pytest.mark.asyncio
async def test_follow_nonexistent_user(client, test_user):
    """
    Test of follow to a non-existent user
    """
    response = await client.post(
        "/api/users/9999/follow", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unfollow_user(client, test_user, db_session):
    """
    Test of unfollow user
    """
    follow_user = User(
        username="followuser",
        api_key="followapikey",
        name="Follow User",
        email="followuser@example.com",
        created_at=datetime.utcnow(),
    )
    db_session.add(follow_user)
    await db_session.commit()
    await db_session.refresh(follow_user)

    follow_record = Follow(user_id=test_user.id, follower_id=follow_user.id)
    db_session.add(follow_record)
    await db_session.commit()

    response = await client.delete(
        f"/api/users/{follow_user.id}/follow", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 200, response.text

    json_response = response.json()
    assert json_response["result"] is True

    follow_check = await db_session.execute(
        select(Follow).where(
            Follow.user_id == test_user.id, Follow.follower_id == follow_user.id
        )
    )
    assert follow_check.scalars().first() is None


@pytest.mark.asyncio
async def test_unfollow_not_following(client, test_user, db_session):
    """
    Test of unfollow not following user
    """
    follow_user = User(
        username="followuser",
        api_key="followapikey",
        name="Follow User",
        email="followuser@example.com",
        created_at=datetime.utcnow(),
    )
    db_session.add(follow_user)
    await db_session.commit()
    await db_session.refresh(follow_user)

    response = await client.delete(
        f"/api/users/{follow_user.id}/follow", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 400, response.text

    json_response = response.json()
    assert json_response["detail"] == "You are not following this user"


@pytest.mark.asyncio
async def test_unfollow_nonexistent_user(client, test_user):
    """
    Test of unfollow to a non-existent user
    """
    response = await client.delete(
        "/api/users/9999/follow", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_like_to_tweet(client, test_user, db_session):
    """
    Test of like to tweet
    """
    tweet = Tweet(content="This is a test tweet", user_id=test_user.id)
    db_session.add(tweet)
    await db_session.commit()
    await db_session.refresh(tweet)

    response = await client.post(
        f"/api/tweets/{tweet.id}/likes", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 200, response.text
    json_response = response.json()
    assert json_response["result"] is True

    likes = await db_session.execute(
        select(Like).where(Like.user_id == test_user.id, Like.tweet_id == tweet.id)
    )
    assert likes.scalars().first() is not None


@pytest.mark.asyncio
async def test_like_nonexistent_tweet(client, test_user):
    """
    Test of like to a non-existent tweet
    """
    response = await client.post(
        "/api/tweets/9999/likes", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remove_like(client, test_user, db_session):
    """
    Test of remove like
    """
    tweet = Tweet(content="This is a test tweet", user_id=test_user.id)
    db_session.add(tweet)
    await db_session.commit()
    await db_session.refresh(tweet)

    await client.post(
        f"/api/tweets/{tweet.id}/likes", headers={"api-key": test_user.api_key}
    )

    response = await client.delete(
        f"/api/tweets/{tweet.id}/likes", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 200, response.text
    json_response = response.json()
    assert json_response["result"] is True

    likes = await db_session.execute(
        select(Like).where(Like.user_id == test_user.id, Like.tweet_id == tweet.id)
    )
    assert likes.scalars().first() is None


@pytest.mark.asyncio
async def test_remove_like_nonexistent_tweet(client, test_user):
    """
    Test of remove like to a non-existent tweet
    """
    response = await client.delete(
        "/api/tweets/9999/likes", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_tweets_by_followings(client, test_user, db_session):
    """
    Test of get tweets by followings
    """
    user2 = User(
        name="User2",
        api_key="test_api_key_2",
        username="Username2",
        email="email2@example.com",
    )
    user3 = User(
        name="User3",
        api_key="test_api_key_3",
        username="Username3",
        email="email3@example.com",
    )
    db_session.add_all([user2, user3])
    await db_session.commit()

    tweet1 = Tweet(content="Tweet by User2", user_id=user2.id)
    tweet2 = Tweet(content="Tweet by User3", user_id=user3.id)
    db_session.add_all([tweet1, tweet2])
    await db_session.commit()

    follow1 = Follow(user_id=test_user.id, follower_id=user2.id)
    follow2 = Follow(user_id=test_user.id, follower_id=user3.id)
    db_session.add_all([follow1, follow2])
    await db_session.commit()

    response = await client.get("/api/tweets", headers={"api-key": test_user.api_key})
    assert response.status_code == 200, response.text
    json_response = response.json()
    assert json_response["result"] is True
    assert len(json_response["tweets"]) == 2


@pytest.mark.asyncio
async def test_get_user_info(client, test_user):
    """
    Test of get user info
    """
    response = await client.get("/api/users/me", headers={"api-key": test_user.api_key})
    assert response.status_code == 200, response.text
    json_response = response.json()
    assert json_response["result"] is True
    assert json_response["user"]["id"] == test_user.id
    assert json_response["user"]["name"] == test_user.name


@pytest.mark.asyncio
async def test_get_user_info_by_id(client, test_user, db_session):
    """
    Test of get user info by id
    """
    user2 = User(
        name="User2",
        api_key="test_api_key_2",
        username="Username2",
        email="email2@example.com",
    )
    db_session.add(user2)
    await db_session.commit()

    response = await client.get(
        f"/api/users/{user2.id}", headers={"api-key": test_user.api_key}
    )
    assert response.status_code == 200, response.text
    json_response = response.json()
    assert json_response["result"] is True
    assert json_response["user"]["id"] == user2.id
    assert json_response["user"]["name"] == user2.name

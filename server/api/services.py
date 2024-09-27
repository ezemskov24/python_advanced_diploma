from typing import List

from fastapi import Depends, HTTPException, Header
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, Follow
from .schemas import UserOut
from server.database.db_connection import get_db


async def get_current_user(
    db: AsyncSession = Depends(get_db), api_key: str = Header(...)
) -> User:
    """
    Retrieve the current user based on the provided API key.

    Args:
        db (AsyncSession): Database session.
        api_key (str): API key provided in the request header.

    Raises:
        HTTPException: If the API key is invalid.

    Returns:
        User: The user object corresponding to the API key.
    """
    user = await db.execute(select(User).where(User.api_key == api_key))
    user = user.scalars().first()

    if user is None:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return user


async def get_user_by_id(user_id: int, db: AsyncSession) -> User:
    """
    Retrieve a user by their ID.

    Args:
        user_id (int): The ID of the user to retrieve.
        db (AsyncSession): Database session.

    Raises:
        HTTPException: If the user with the given ID is not found.

    Returns:
        User: The user object corresponding to the provided ID.
    """
    user_select = await db.execute(select(User).where(User.id == user_id))
    user = user_select.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


async def get_followers(user: User, db: AsyncSession) -> List[UserOut]:
    """
    Retrieve a list of followers for a given user.

    Args:
        user (User): The user for whom to retrieve followers.
        db (AsyncSession): Database session.

    Returns:
        List[UserOut]: A list of users who follow the given user.
    """
    followers_query = await db.execute(
        select(User)
        .join(Follow, Follow.user_id == User.id)
        .where(Follow.follower_id == user.id)
    )
    return [
        UserOut(id=follower.id, name=follower.name)
        for follower in followers_query.scalars().all()
    ]


async def get_followings(user: User, db: AsyncSession) -> List[UserOut]:
    """
    Retrieve a list of users followed by a given user.

    Args:
        user (User): The user whose followings are to be retrieved.
        db (AsyncSession): Database session.

    Returns:
        List[UserOut]: A list of users that the given user is following.
    """
    followings_query = await db.execute(
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.user_id == user.id)
    )
    return [
        UserOut(id=following.id, name=following.name)
        for following in followings_query.scalars().all()
    ]

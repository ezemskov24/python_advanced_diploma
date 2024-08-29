from fastapi import Depends, HTTPException, Header
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, Follow
from .schemas import UserOut
from database.db_connection import get_db


async def get_current_user(
    db: AsyncSession = Depends(get_db), api_key: str = Header(...)
):
    user = await db.execute(select(User).where(User.api_key == api_key))
    user = user.scalars().first()

    if user is None:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return user


async def get_user_by_id(user_id: int, db: AsyncSession):
    user_select = await db.execute(select(User).where(User.id == user_id))
    user = user_select.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user

async def get_followers(user: User, db: AsyncSession):
    followers_query = await db.execute(
        select(User)
        .join(Follow, Follow.user_id == User.id)
        .where(Follow.follower_id == user.id)
    )
    return [
        UserOut(id=follower.id, name=follower.name)
        for follower in followers_query.scalars().all()
    ]


async def get_followings(user: User, db: AsyncSession):
    followings_query = await db.execute(
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.user_id == user.id)
    )
    return [
        UserOut(id=following.id, name=following.name)
        for following in followings_query.scalars().all()
    ]

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import engine, AsyncSessionLocal, Base
from models import Tweet, Like, User, Follow
from schemas import TweetIn, TweetResponse, UserOut, TweetOut, UserResponse


@asynccontextmanager
async def lifespan(application: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


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


async def tweet_query(idx: int, db: AsyncSession = Depends(get_db)):

    tweet_select = await db.execute(select(Tweet).where(Tweet.id == idx))
    tweet = tweet_select.scalars().first()

    return tweet


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


@app.post("/api/tweets")
async def post_new_tweet(
    tweet: TweetIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    new_tweet = Tweet(**tweet.model_dump(), user_id=user.id)

    db.add(new_tweet)
    await db.commit()
    return {"result": True, "tweet_id": new_tweet.id}


@app.delete("/api/tweets/{idx}")
async def delete_own_tweet(
    idx: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    tweet = await db.get(Tweet, idx)

    if tweet is None:
        raise HTTPException(status_code=404, detail="Tweet not found")

    if tweet.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="You can only delete your own tweets"
        )

    await db.delete(tweet)
    await db.commit()

    return {"result": True}


@app.post("/api/users/{idx}/follow")
async def follow_user(
    idx: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    follower = await get_user_by_id(idx, db)

    if user.id == follower.id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")

    existing_follow = await db.execute(
        select(Follow).where(
            Follow.user_id == user.id, Follow.follower_id == follower.id
        )
    )
    if existing_follow.scalars().first():
        raise HTTPException(
            status_code=400, detail="You are already following this user"
        )

    new_follow = Follow(user_id=user.id, follower_id=follower.id)

    db.add(new_follow)
    await db.commit()

    return {"result": True}


@app.delete("/api/users/{idx}/follow")
async def unfollow_user(
    idx: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    follower = await get_user_by_id(idx, db)

    existing_follow = await db.execute(
        select(Follow).where(
            Follow.user_id == user.id, Follow.follower_id == follower.id
        )
    )
    follow = existing_follow.scalars().first()

    if not follow:
        raise HTTPException(status_code=400, detail="You are not following this user")

    await db.delete(follow)
    await db.commit()

    return {"result": True}


@app.post("/api/tweets/{idx}/likes")
async def like_to_tweet(
    idx: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    tweet = await db.get(Tweet, idx)

    if tweet is None:
        raise HTTPException(status_code=404, detail="Tweet not found")

    existing_like = await db.execute(
        select(Like).where(Like.user_id == user.id, Like.tweet_id == tweet.id)
    )
    if existing_like.scalars().first():
        raise HTTPException(status_code=400, detail="You have already liked this tweet")

    new_like = Like(user_id=user.id, tweet_id=tweet.id)

    db.add(new_like)
    await db.commit()

    return {"result": True}


@app.delete("/api/tweets/{idx}/likes")
async def remove_like(
    idx: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    tweet = await db.get(Tweet, idx)

    if tweet is None:
        raise HTTPException(status_code=404, detail="Tweet not found")

    existing_like = await db.execute(
        select(Like).where(Like.user_id == user.id, Like.tweet_id == tweet.id)
    )
    like = existing_like.scalars().first()

    if not like:
        raise HTTPException(status_code=400, detail="You haven't liked this tweet yet")

    await db.delete(like)
    await db.commit()

    return {"result": True}


@app.get("/api/tweets")
async def get_tweets_by_followings(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    following_query = await db.execute(
        select(Follow.follower_id).where(Follow.user_id == user.id)
    )
    following_ids = following_query.scalars().all()

    tweets_by_following = await db.execute(
        select(Tweet)
        .options(selectinload(Tweet.user), selectinload(Tweet.likes))
        .outerjoin(Like)
        .where(Tweet.user_id.in_(following_ids))
        .group_by(Tweet.id)
        .order_by(func.count(Like.id).desc())
    )

    result_tweets = [
        TweetOut(
            id=tweet.id,
            content=tweet.content,
            attachments=tweet.attachment,
            user=UserOut(id=tweet.user.id, name=tweet.user.name),
            likes=[
                {
                    "user_id": like.user_id,
                    "name": (await db.get(User, like.user_id)).name,
                }
                for like in tweet.likes
            ],
        )
        for tweet in tweets_by_following.scalars().all()
    ]

    return TweetResponse(result=True, tweets=result_tweets)


@app.get("/api/users/me")
async def get_user_info(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    followers = await get_followers(user, db)
    followings = await get_followings(user, db)

    user_out = UserOut(id=user.id, name=user.name)

    return UserResponse(
        result=True, user=user_out, followers=followers, followings=followings
    )


@app.get("/api/users/{idx}")
async def get_user_info_by_id(idx: int, db: AsyncSession = Depends(get_db)):

    user = await get_user_by_id(idx, db)

    followers = await get_followers(user, db)
    followings = await get_followings(user, db)

    user_out = UserOut(id=user.id, name=user.name)

    return UserResponse(
        result=True, user=user_out, followers=followers, followings=followings
    )

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.db_connection import get_db
from .models import Tweet, Like, User, Follow
from .schemas import TweetIn, TweetResponse, UserOut, TweetOut, UserResponse
from .services import get_current_user, get_user_by_id, get_followers, get_followings

router: APIRouter = APIRouter(
    prefix="/api",
)


@router.post("/tweets")
async def post_new_tweet(
    tweet: TweetIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    new_tweet = Tweet(**tweet.model_dump(), user_id=user.id)

    db.add(new_tweet)
    await db.commit()
    return {"result": True, "tweet_id": new_tweet.id}


@router.delete("/tweets/{idx}")
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


@router.post("/users/{idx}/follow")
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


@router.delete("/users/{idx}/follow")
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


@router.post("/tweets/{idx}/likes")
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


@router.delete("/tweets/{idx}/likes")
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


@router.get("/tweets")
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


@router.get("/users/me")
async def get_user_info(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    followers = await get_followers(user, db)
    followings = await get_followings(user, db)

    user_out = UserOut(id=user.id, name=user.name)

    return UserResponse(
        result=True, user=user_out, followers=followers, followings=followings
    )


@router.get("/users/{idx}")
async def get_user_info_by_id(idx: int, db: AsyncSession = Depends(get_db)):

    user = await get_user_by_id(idx, db)

    followers = await get_followers(user, db)
    followings = await get_followings(user, db)

    user_out = UserOut(id=user.id, name=user.name)

    return UserResponse(
        result=True, user=user_out, followers=followers, followings=followings
    )

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request
from typing import Annotated, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from authx import RequestToken
import hashlib
import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from models import Base, UserModel, PostModel, LikeModel, CommentModel
from schemas import UserRegisterSchema, UserLoginSchema, UserResponseSchema, PostCreateSchema, PostResponseSchema, \
                    CommentSchema, CommentResponseSchema, LikeResponseSchema
from database import get_sessions, engine
from jwt_authx import auth, get_payload_from_token, verify_token


app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

SessionDep = Annotated[AsyncSession, Depends(get_sessions)]


@app.post('/register', tags=['Пользователь 😀'])
@limiter.limit("2/minute")
async def register(
        creds: UserRegisterSchema,
        request: Request,  # noqa
        session: SessionDep) -> dict:
    query = select(UserModel).where(creds.username == UserModel.username)
    result = await session.execute(query)
    if result.scalar():
        raise HTTPException(status_code=401, detail='Users exists')
    password_hash = hashlib.md5(creds.password.encode()).hexdigest()
    new_user = UserModel(
        username=creds.username,
        password=password_hash,
        bio=creds.bio,
        age=creds.age,
        role='user'
    )
    session.add(new_user)
    await session.commit()
    return {'ok': True}


@app.post('/login', tags=['Пользователь 😀'])
@limiter.limit("5/minute")
async def login(
        creds: UserLoginSchema,
        request: Request,  # noqa
        session: SessionDep) -> dict:
    query = select(UserModel).where(creds.username == UserModel.username)
    result = await session.execute(query)
    db_user = result.scalar()
    if not db_user:
        raise HTTPException(status_code=401, detail='Incorrect username')

    password_hash = hashlib.md5(creds.password.encode()).hexdigest()
    if db_user.password == password_hash:
        token = auth.create_access_token(
            uid=str(db_user.id),
            data={
                "role": db_user.role,
            }
        )
        get_payload_from_token(token)
        return {'access_token': token}
    raise HTTPException(status_code=401, detail='Incorrect password')


@app.get('/users', dependencies=[Depends(auth.get_token_from_request)], tags=['Пользователь 😀'])
@limiter.limit("5/15 seconds")
async def get_users(
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> List[UserResponseSchema]:
    await verify_token(token, session)

    query = select(UserModel)
    results = await session.execute(query)
    new_results = []
    for result in results.scalars().all():
        new_results.append(
            UserResponseSchema(user_id=result.id, username=result.username, bio=result.bio, age=result.age)
        )
    return new_results


@app.get('/users/{user_id}', dependencies=[Depends(auth.get_token_from_request)], tags=['Пользователь 😀'])
@limiter.limit("5/15 seconds")
async def get_user_with_id(
        user_id: int,
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> UserResponseSchema:
    await verify_token(token, session)

    query = select(UserModel).where(user_id == UserModel.id)
    db_user = await session.execute(query)
    db_user = db_user.scalar()
    if db_user:
        return UserResponseSchema(user_id=db_user.id, username=db_user.username, bio=db_user.bio, age=db_user.age)
    raise HTTPException(status_code=404, detail='User not found')


@app.delete('/users', dependencies=[Depends(auth.get_token_from_request)], tags=['Пользователь 😀'])
@limiter.limit("5/30 seconds")
async def delete_user(
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> dict:
    await verify_token(token, session)

    uid = get_payload_from_token(token.token)['sub']
    query = select(UserModel).where(UserModel.id == uid)
    result = await session.execute(query)
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    await session.delete(user)

    query = select(PostModel).where(PostModel.author_id == uid)
    result = await session.execute(query)
    for post in result.scalars().all():
        await session.delete(post)

    query = select(LikeModel).where(LikeModel.author_id == uid)
    result = await session.execute(query)
    for like in result.scalars().all():
        await session.delete(like)

    query = select(CommentModel).where(CommentModel.author_id == uid)
    result = await session.execute(query)
    for comment in result.scalars().all():
        await session.delete(comment)

    await session.commit()
    return {'ok': True}


@app.post('/posts', dependencies=[Depends(auth.get_token_from_request)], tags=['Пост ✉️'])
@limiter.limit("5/minute")
async def create_post(
        post: PostCreateSchema,
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> dict:
    await verify_token(token, session)

    uid = get_payload_from_token(token.token)['sub']

    query = select(UserModel).where(int(uid) == UserModel.id)
    result = await session.execute(query)
    db_user = result.scalar()
    if not db_user:
        raise HTTPException(status_code=404, detail='User not found')

    db_post = PostModel(author_id=uid, title=post.title, body=post.body)
    session.add(db_post)
    await session.commit()
    return {'ok': True}


@app.get('/posts', dependencies=[Depends(auth.get_token_from_request)], tags=['Пост ✉️'])
@limiter.limit("5/15 seconds")
async def get_posts(
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> List[PostResponseSchema]:
    await verify_token(token, session)

    query = select(PostModel)
    post_results = await session.execute(query)
    new_results = []
    for post_result in post_results.scalars().all():
        query = select(LikeModel).where(post_result.id == LikeModel.post_id)
        like_results = await session.execute(query)
        likes = len(like_results.fetchall())

        new_results.append(
            PostResponseSchema(
                post_id=post_result.id,
                author_id=post_result.author_id,
                title=post_result.title,
                body=post_result.body,
                likes=likes)
        )
    return new_results


@app.get('/posts/{post_id}', dependencies=[Depends(auth.get_token_from_request)], tags=['Пост ✉️'])
@limiter.limit("5/15 seconds")
async def get_post_with_id(
        post_id: int,
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> PostResponseSchema:
    await verify_token(token, session)

    query = select(PostModel).where(post_id == PostModel.id)
    result = await session.execute(query)
    post = result.scalar()
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')

    query = select(LikeModel).where(post_id == LikeModel.post_id)
    like_results = await session.execute(query)
    likes = len(like_results.fetchall())

    return PostResponseSchema(
        post_id=post.id,
        author_id=post.author_id,
        title=post.title,
        body=post.body,
        likes=likes
    )


@app.delete('/posts', dependencies=[Depends(auth.get_token_from_request)], tags=['Пост ✉️'])
@limiter.limit("5/30 seconds")
async def delete_post(
        post_id: int,
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> dict:
    await verify_token(token, session)

    query = select(PostModel).where(PostModel.id == post_id)
    result = await session.execute(query)
    post = result.scalar()
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')

    uid = get_payload_from_token(token.token)['sub']
    if post.author_id != int(uid):
        raise HTTPException(status_code=401, detail='This post is not yours')

    await session.delete(post)

    query = select(LikeModel).where(LikeModel.post_id == post_id)
    result = await session.execute(query)
    for like in result.scalars().all():
        await session.delete(like)

    query = select(CommentModel).where(CommentModel.post_id == post_id)
    result = await session.execute(query)
    for comment in result.scalars().all():
        await session.delete(comment)

    await session.commit()
    return {'ok': True}


@app.post('/likes', dependencies=[Depends(auth.get_token_from_request)], tags=['Лайк 💘'])
@limiter.limit("5/30 seconds")
async def put_like(
        post_id: int,
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> dict:
    await verify_token(token, session)

    uid = get_payload_from_token(token.token)['sub']

    query = select(PostModel).where(PostModel.id == post_id)
    result = await session.execute(query)
    if not result.scalar():
        raise HTTPException(status_code=404, detail='Post not found')

    query = select(LikeModel).where(LikeModel.author_id == uid).where(LikeModel.post_id == post_id)
    result = await session.execute(query)
    if result.scalar():
        raise HTTPException(status_code=401, detail='Like already given')

    like = LikeModel(post_id=post_id, author_id=uid)
    session.add(like)
    await session.commit()
    return {'ok': True}


@app.get('/likes', dependencies=[Depends(auth.get_token_from_request)], tags=['Лайк 💘'])
@limiter.limit("5/15 seconds")
async def get_likes(
        post_id: int,
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> List[LikeResponseSchema]:
    await verify_token(token, session)

    query = select(PostModel).where(PostModel.id == post_id)
    result = await session.execute(query)
    if not result.scalar():
        raise HTTPException(status_code=404, detail='Post not found')

    query = select(LikeModel).where(LikeModel.post_id == post_id)
    results = await session.execute(query)
    new_results = []
    for result in results.scalars().all():
        new_results.append(
            LikeResponseSchema(like_id=result.id, post_id=post_id, author_id=result.author_id)
        )
    return new_results


@app.delete('/likes', dependencies=[Depends(auth.get_token_from_request)], tags=['Лайк 💘'])
@limiter.limit("5/30 seconds")
async def delete_like(
        like_id: int,
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> dict:
    await verify_token(token, session)

    query = select(LikeModel).where(LikeModel.id == like_id)
    result = await session.execute(query)
    comment = result.scalar()
    if not comment:
        raise HTTPException(status_code=404, detail='Like not found')

    uid = get_payload_from_token(token.token)['sub']
    if comment.author_id != int(uid):
        raise HTTPException(status_code=401, detail='This like is not yours')

    await session.delete(comment)
    await session.commit()
    return {'ok': True}


@app.post('/comments', dependencies=[Depends(auth.get_token_from_request)], tags=['Комментарий ✒️'])
@limiter.limit("5/30 seconds")
async def add_comment(
        comment: CommentSchema,
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> dict:
    await verify_token(token, session)

    query = select(PostModel).where(PostModel.id == comment.post_id)
    result = await session.execute(query)
    if not result.scalar():
        raise HTTPException(status_code=404, detail='Post not found')

    uid = get_payload_from_token(token.token)['sub']

    db_comment = CommentModel(post_id=comment.post_id, author_id=uid, title=comment.title)
    session.add(db_comment)
    await session.commit()
    return {'ok': True}


@app.get('/comments', dependencies=[Depends(auth.get_token_from_request)], tags=['Комментарий ✒️'])
@limiter.limit("5/15 seconds")
async def get_comments(
        post_id: int,
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> List[CommentResponseSchema]:
    await verify_token(token, session)

    query = select(PostModel).where(PostModel.id == post_id)
    result = await session.execute(query)
    if not result.scalar():
        raise HTTPException(status_code=404, detail='Post not found')

    query = select(CommentModel).where(CommentModel.post_id == post_id)
    results = await session.execute(query)
    new_results = []
    for result in results.scalars().all():
        new_results.append(
            CommentResponseSchema(comment_id=result.id, post_id=post_id, title=result.title, author_id=result.author_id)
        )
    return new_results


@app.delete('/comments', dependencies=[Depends(auth.get_token_from_request)], tags=['Комментарий ✒️'])
@limiter.limit("5/30 seconds")
async def delete_comment(
        comment_id: int,
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> dict:
    await verify_token(token, session)

    query = select(CommentModel).where(CommentModel.id == comment_id)
    result = await session.execute(query)
    comment = result.scalar()
    if not comment:
        raise HTTPException(status_code=404, detail='Comment not found')

    uid = get_payload_from_token(token.token)['sub']
    if comment.author_id != int(uid):
        raise HTTPException(status_code=401, detail='This comment is not yours')

    await session.delete(comment)
    await session.commit()
    return {'ok': True}


@app.post('/admin/drop_and_create_database', dependencies=[Depends(auth.get_token_from_request)], tags=['Админ ✨'])
@limiter.limit("5/minute")
async def admin_setup_database(
        request: Request,  # noqa
        session: SessionDep,
        token: RequestToken = Depends()) -> dict:
    if not os.path.exists('database.db'):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        return {'ok': True}
    uid = get_payload_from_token(token.token)['sub']
    query = select(UserModel).where(UserModel.id == uid)
    result = await session.execute(query)
    if result.scalar().role != 'admin':
        raise HTTPException(status_code=403, detail='You are not admin')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {'ok': True}


@app.delete('/admin/delete_comment', dependencies=[Depends(auth.get_token_from_request)], tags=['Админ ✨'])
@limiter.limit("5/30 seconds")
async def admin_delete_comment(
        comment_id: int,
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> dict:
    await verify_token(token, session)

    uid = get_payload_from_token(token.token)['sub']
    query = select(UserModel).where(UserModel.id == uid)
    result = await session.execute(query)
    if result.scalar().role != 'admin':
        raise HTTPException(status_code=403, detail='You are not admin')

    query = select(CommentModel).where(CommentModel.id == comment_id)
    result = await session.execute(query)
    comment = result.scalar()
    if not comment:
        raise HTTPException(status_code=404, detail='Comment not found')

    await session.delete(comment)
    await session.commit()
    return {'ok': True}


@app.delete('/admin/delete_like', dependencies=[Depends(auth.get_token_from_request)], tags=['Админ ✨'])
@limiter.limit("5/30 seconds")
async def admin_delete_like(
        like_id: int,
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> dict:
    await verify_token(token, session)

    uid = get_payload_from_token(token.token)['sub']
    query = select(UserModel).where(UserModel.id == uid)
    result = await session.execute(query)
    if result.scalar().role != 'admin':
        raise HTTPException(status_code=403, detail='You are not admin')

    query = select(LikeModel).where(LikeModel.id == like_id)
    result = await session.execute(query)
    comment = result.scalar()
    if not comment:
        raise HTTPException(status_code=404, detail='Like not found')

    await session.delete(comment)
    await session.commit()
    return {'ok': True}


@app.delete('/admin/delete_user', dependencies=[Depends(auth.get_token_from_request)], tags=['Админ ✨'])
@limiter.limit("5/30 seconds")
async def delete_user(
        user_id: int,
        session: SessionDep,
        request: Request,  # noqa
        token: RequestToken = Depends()) -> dict:
    await verify_token(token, session)

    query = select(UserModel).where(UserModel.id == user_id)
    result = await session.execute(query)
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    await session.delete(user)

    query = select(PostModel).where(PostModel.author_id == user_id)
    result = await session.execute(query)
    for post in result.scalars().all():
        await session.delete(post)

    query = select(LikeModel).where(LikeModel.author_id == user_id)
    result = await session.execute(query)
    for like in result.scalars().all():
        await session.delete(like)

    query = select(CommentModel).where(CommentModel.author_id == user_id)
    result = await session.execute(query)
    for comment in result.scalars().all():
        await session.delete(comment)

    await session.commit()
    return {'ok': True}



if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)

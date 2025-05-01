from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from authx import RequestToken
import hashlib
from typing import Annotated, List

from models import Base, UserModel, PostModel
from schemas import UserRegisterSchema, UserLoginSchema, PostCreateSchema, PostResponseSchema, UserResponseSchema
from database import get_sessions, engine
from jwt_authx import auth, get_payload_from_token, verify_token

app = FastAPI()
SessionDep = Annotated[AsyncSession, Depends(get_sessions)]


@app.post('/setup_database')
async def setup_database() -> dict:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {'ok': True}


@app.post('/register')
async def register(
        creds: UserRegisterSchema,
        session: SessionDep) -> dict:
    query = select(UserModel).where(creds.username == UserModel.username)
    result = await session.execute(query)
    if result.scalar():
        raise HTTPException(status_code=403, detail='Users exists')
    password_hash = hashlib.md5(creds.password.encode()).hexdigest()
    new_user = UserModel(
        username=creds.username,
        password=password_hash,
        bio=creds.bio,
        age=creds.age
    )
    session.add(new_user)
    await session.commit()
    return {'ok': True}


@app.post('/login')
async def login(
        creds: UserLoginSchema,
        session: SessionDep) -> dict:
    query = select(UserModel).where(creds.username == UserModel.username)
    result = await session.execute(query)
    db_user = result.scalar()
    if not db_user:
        raise HTTPException(status_code=403, detail='Incorrect username')

    password_hash = hashlib.md5(creds.password.encode()).hexdigest()
    print(db_user.password)
    if db_user.password == password_hash:
        token = auth.create_access_token(uid=str(db_user.id))
        return {'access_token': token}
    raise HTTPException(status_code=403, detail='Incorrect password')


@app.get('/users', dependencies=[Depends(auth.get_token_from_request)])
async def get_users(
        session: SessionDep,
        token: RequestToken = Depends()) -> List[UserResponseSchema]:
    verify_token(token)

    query = select(UserModel)
    results = await session.execute(query)
    new_results = []
    for result in results.scalars().all():
        new_results.append(
            UserResponseSchema(id=result.id, username=result.username, bio=result.bio, age=result.age)
        )
    return new_results


@app.get('/users/{user_id}', dependencies=[Depends(auth.get_token_from_request)])
async def get_user_with_id(
        user_id: int,
        session: SessionDep,
        token: RequestToken = Depends()) -> UserResponseSchema:
    verify_token(token)

    query = select(UserModel).where(user_id == UserModel.id)
    db_user = await session.execute(query)
    db_user = db_user.scalar()
    if db_user:
        return UserResponseSchema(id=db_user.id, username=db_user.username, bio=db_user.bio, age=db_user.age)
    raise HTTPException(status_code=404, detail='User not found')


@app.post('/posts', dependencies=[Depends(auth.get_token_from_request)])
async def create_post(
        post: PostCreateSchema,
        session: SessionDep,
        token: RequestToken = Depends()) -> dict:
    verify_token(token)

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


@app.get('/posts', dependencies=[Depends(auth.get_token_from_request)])
async def get_posts(
        session: SessionDep,
        token: RequestToken = Depends()) -> List[PostResponseSchema]:
    verify_token(token)

    query = select(PostModel)
    results = await session.execute(query)
    new_results = []
    for result in results.scalars().all():
        new_results.append(
            PostResponseSchema(id=result.id, author_id=result.author_id, title=result.title, body=result.body)
        )
    return new_results


@app.get('/posts/{post_id}', dependencies=[Depends(auth.get_token_from_request)])
async def get_post_with_id(
        post_id: int,
        session: SessionDep,
        token: RequestToken = Depends()) -> PostResponseSchema:
    verify_token(token)

    query = select(PostModel).where(post_id == PostModel.id)
    result = await session.execute(query)
    post = result.scalar()
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    return PostResponseSchema(id=post.id, author_id=post.author_id, title=post.title, body=post.body)


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)

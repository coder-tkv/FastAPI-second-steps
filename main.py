from sqlalchemy import select
from sqlalchemy.orm import Session
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from authx import RequestToken
import hashlib

from models import Base, UserModel, PostModel
from schemas import UserRegisterSchema, UserLoginSchema, PostCreateSchema
from database import engine, session_local
from jwt_authx import auth, get_payload_from_token


app = FastAPI()

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def get_sessions():
    db = session_local()
    try:
        yield db
    finally:
        db.close()


@app.post('/register')
def register(creds: UserRegisterSchema, session: Session = Depends(get_sessions)) -> dict:
    db_user = session.query(UserModel).filter(creds.username == UserModel.username).first()
    if db_user:
        raise HTTPException(status_code=403, detail='Users exists')
    password_hash = hashlib.md5(creds.password.encode()).hexdigest()
    print(password_hash)
    new_user = UserModel(
        username=creds.username,
        password=password_hash,
        bio=creds.bio,
        age=creds.age
    )
    session.add(new_user)
    session.commit()
    return {'ok': True}


@app.post('/login')
def login(creds: UserLoginSchema, session: Session = Depends(get_sessions)) -> dict:
    db_user = session.query(UserModel).filter(creds.username == UserModel.username).first()
    if db_user is None:
        raise HTTPException(status_code=403, detail='Incorrect username')
    password_hash = hashlib.md5(creds.password.encode()).hexdigest()
    if db_user.password == password_hash:
        print(db_user.id)
        token = auth.create_access_token(uid=str(db_user.id))
        return {'access_token': token}
    raise HTTPException(status_code=403, detail='Incorrect password')


@app.get('/users', dependencies=[Depends(auth.get_token_from_request)])
def get_users(session: Session = Depends(get_sessions), token: RequestToken = Depends()):
    try:
        auth.verify_token(token=token)
    except Exception as e:
        raise HTTPException(401, detail={"message": str(e)}) from e

    query = select(UserModel)
    results = session.execute(query)
    new_results = []
    for result in results.scalars().all():
        new_results.append(
            {
                'username': result.username,
                'bio': result.bio,
                'age': result.age,
            }
        )
    return new_results


@app.get('/users/{user_id}', dependencies=[Depends(auth.get_token_from_request)])
def get_user_with_id(user_id: int, session: Session = Depends(get_sessions), token: RequestToken = Depends()):
    try:
        auth.verify_token(token=token)
    except Exception as e:
        raise HTTPException(401, detail={"message": str(e)}) from e

    db_user = session.query(UserModel).filter(user_id == UserModel.id)
    if db_user.scalar() is None:
        raise HTTPException(status_code=404, detail='User not found')

    return db_user.scalar()


@app.post('/posts', dependencies=[Depends(auth.get_token_from_request)])
def create_post(post: PostCreateSchema, session: Session = Depends(get_sessions), token: RequestToken = Depends()):
    try:
        auth.verify_token(token=token)
    except Exception as e:
        raise HTTPException(401, detail={"message": str(e)}) from e

    uid = get_payload_from_token(token.token)['sub']

    db_user = session.query(UserModel).filter(int(uid) == UserModel.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail='User not found')

    db_post = PostModel(author_id=uid, title=post.title, body=post.body)
    session.add(db_post)
    session.commit()
    return {'ok': True}


@app.get('/posts', dependencies=[Depends(auth.get_token_from_request)])
def get_posts(session: Session = Depends(get_sessions), token: RequestToken = Depends()):
    try:
        auth.verify_token(token=token)
    except Exception as e:
        raise HTTPException(401, detail={"message": str(e)}) from e

    query = select(PostModel)
    result = session.execute(query)
    return result.scalars().all()


@app.get('/posts/{post_id}', dependencies=[Depends(auth.get_token_from_request)])
def get_post_with_id(post_id: int, session: Session = Depends(get_sessions), token: RequestToken = Depends()):
    try:
        auth.verify_token(token=token)
    except Exception as e:
        raise HTTPException(401, detail={"message": str(e)}) from e

    post = session.query(PostModel).filter(post_id == PostModel.author_id)
    if post.scalar() is None:
        raise HTTPException(status_code=404, detail='Post not found')
    return post.scalar()


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)

import jwt
from jwt import PyJWTError
from authx import AuthX, AuthXConfig
from fastapi import HTTPException
from sqlalchemy import select
from models import UserModel

config = AuthXConfig()
config.JWT_SECRET_KEY = 'SECRET_KEY'
config.JWT_ACCESS_COOKIE_NAME = 'my_access_token'
config.JWT_TOKEN_LOCATION = ['headers']
auth = AuthX(config=config)


def get_payload_from_token(token: str):
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        return payload
    except PyJWTError:
        raise HTTPException(401, detail="Invalid token")


async def verify_token(token, session):
    try:
        auth.verify_token(token=token)
    except Exception as e:
        raise HTTPException(401, detail={"message": str(e)}) from e

    uid = get_payload_from_token(token.token)['sub']
    query = select(UserModel).where(UserModel.id == uid)
    result = await session.execute(query)
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=404, detail='Invalid token')
    return True

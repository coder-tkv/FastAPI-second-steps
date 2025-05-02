import jwt
from jwt import PyJWTError
from authx import AuthX, AuthXConfig
from fastapi import HTTPException

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


def verify_token(token):
    try:
        auth.verify_token(token=token)
    except Exception as e:
        raise HTTPException(401, detail={"message": str(e)}) from e

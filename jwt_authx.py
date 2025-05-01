import jwt
from jwt import PyJWTError
from authx import AuthX, AuthXConfig

config = AuthXConfig()
config.JWT_SECRET_KEY = 'SECRET_KEY'
config.JWT_ACCESS_COOKIE_NAME = 'my_access_token'
config.JWT_TOKEN_LOCATION = ['headers']
auth = AuthX(config=config)


def get_payload_from_token(token: str):
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        return payload
    except PyJWTError as e:
        raise ValueError(f"Invalid token: {e}")

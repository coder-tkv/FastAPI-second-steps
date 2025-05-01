from pydantic import BaseModel


class UserRegisterSchema(BaseModel):
    username: str
    password: str
    bio: str
    age: int


class UserLoginSchema(BaseModel):
    username: str
    password: str


class PostCreateSchema(BaseModel):
    title: str
    body: str

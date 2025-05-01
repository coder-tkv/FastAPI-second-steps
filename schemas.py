from pydantic import BaseModel


class UserSchema(BaseModel):
    username: str
    bio: str
    age: int


class UserResponseSchema(UserSchema):
    id: int


class UserRegisterSchema(UserSchema):
    password: str


class UserLoginSchema(BaseModel):
    username: str
    password: str


class PostCreateSchema(BaseModel):
    title: str
    body: str


class PostResponseSchema(PostCreateSchema):
    id: int
    author_id: int

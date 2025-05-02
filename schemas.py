from pydantic import BaseModel


class UserSchema(BaseModel):
    username: str
    bio: str
    age: int


class UserResponseSchema(UserSchema):
    user_id: int


class UserRegisterSchema(UserSchema):
    password: str


class UserLoginSchema(BaseModel):
    username: str
    password: str


class PostCreateSchema(BaseModel):
    title: str
    body: str


class PostResponseSchema(PostCreateSchema):
    post_id: int
    author_id: int
    likes: int


class CommentSchema(BaseModel):
    post_id: int
    title: str


class CommentResponseSchema(CommentSchema):
    comment_id: int
    author_id: int

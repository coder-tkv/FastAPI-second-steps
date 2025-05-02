from sqlalchemy import Column, Integer, String
from database import Base


class UserModel(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    password = Column(String)
    bio = Column(String)
    age = Column(Integer)
    role = Column(String)


class PostModel(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer)
    title = Column(String, index=True)
    body = Column(String)


class LikeModel(Base):
    __tablename__ = 'likes'

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, index=True)
    author_id = Column(Integer)


class CommentModel(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, index=True)
    author_id = Column(Integer)
    title = Column(String)

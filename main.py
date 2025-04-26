from pydantic import BaseModel, Field, EmailStr, ConfigDict
from fastapi import FastAPI


app = FastAPI()

data_wo_age = {
    'email': 'abc@mail.ru',
    'bio': 'Я пирожок',
}


class UserSchema(BaseModel):
    email: EmailStr
    bio: str | None = Field(max_length=10)

    model_config = ConfigDict(extra='forbid')


users = []


@app.post('/users')
async def add_user(user: UserSchema):
    users.append(user)
    return {'ok': True, 'msg': 'Юзер добавлен'}


@app.get('/users')
async def get_users() -> list[UserSchema]:
    return users

from pydantic import BaseModel, Field, EmailStr

data = {
    'email': 'abc@mail.ru',
    'bio': 'Я пирожок',
    'age': 12
}

data_wo_age = {
    'email': 'abc@mail.ru',
    'bio': 'Я пирожок'
}


class UserSchema(BaseModel):
    email: EmailStr
    bio: str | None = Field(max_length=10)


class UserAgeSchema(UserSchema):
    age: int = Field(ge=0, le=130)


user = UserAgeSchema(**data)
user_wo_age = UserSchema(**data_wo_age)
print(repr(user))
print(repr(user_wo_age))

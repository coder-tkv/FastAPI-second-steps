from pydantic import BaseModel, Field, EmailStr

data = {
    'email': 'abc@mail.ru',
    'bio': 'Я вкусный пирожок',
    'age': 12
}


class UserSchema(BaseModel):
    email: EmailStr
    bio: str | None = Field(max_length=10)
    age: int = Field(ge=0, le=130)


user = UserSchema(**data)
print(repr(user))

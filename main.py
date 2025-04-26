from pydantic import BaseModel

data = {
    'email': 'abc@mail',
    'bio': None,
    'age': 12
}


class UserSchema(BaseModel):
    email: str
    bio: str | None
    age: int


print(UserSchema(**data))

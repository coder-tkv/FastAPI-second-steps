from pydantic import BaseModel, Field

data = {
    'email': 'abc@mail',
    'bio': None,
    'age': -12
}


class UserSchema(BaseModel):
    email: str
    bio: str | None
    age: int = Field(ge=0, le=130)


user = UserSchema(**data)
print(user)

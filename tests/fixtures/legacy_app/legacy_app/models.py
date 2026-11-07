from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


class Config:  # old Pydantic v1 style
    extra = "ignore"


def user_to_dict(user: User) -> dict:
    return user.dict()  # old method name

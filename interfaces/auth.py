from pydantic import BaseModel, Field


class RegisterReq(BaseModel):
  username: str = Field(..., min_length=4, max_length=32)
  password: str = Field(..., min_length=6, max_length=48)
  password_verify: str = Field(..., min_length=6, max_length=48)


class User(BaseModel):
  id: int
  username: str

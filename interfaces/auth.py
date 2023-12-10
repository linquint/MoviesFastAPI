from pydantic import BaseModel, Field


class RegisterReq(BaseModel):
  username: str = Field(..., min_length=4, max_length=32)
  password: str = Field(..., min_length=6, max_length=48)
  passwordVerify: str = Field(..., min_length=6, max_length=48)


class User(BaseModel):
  id: int
  username: str
  
  
class LoginResponse(BaseModel):
  access_token: str
  refresh_token: str
  user: User
  
  
class RefreshReq(BaseModel):
  refresh_token: str

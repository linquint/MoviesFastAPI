from pydantic import BaseModel


class LoginReq(BaseModel):
  username: str
  password: str
  
  
class AuthData(BaseModel):
  id: int
  sub: str
  exp: str

from datetime import datetime
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import ValidationError
from db.prisma import prisma as db
import utils.err as err
import utils.helpers as helpers


reuseable_oauth = OAuth2PasswordBearer(
  tokenUrl="/api/login",
  scheme_name="JWT"
)


async def get_current_user(token: str = Depends(reuseable_oauth)):
  try:
    payload = jwt.decode(token, helpers.dot_env("access"), algorithms=["HS256"])
    
    if datetime.fromtimestamp(payload.get("exp")) < datetime.utcnow():
      raise err.credentials_exception
    
    user = await db.users.find_unique(where={"id": payload.get("id")})
    if not user:
      raise err.credentials_exception
    return user
  except(jwt.PyJWTError, ValidationError):
    raise err.credentials_exception
  

import logging
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from interfaces.auth import RegisterReq
import utils.err as err
import utils.helpers as helpers
from db.prisma import prisma as db


router = APIRouter(
  prefix="/api",
  tags=["auth"],
)


@router.post("/register", response_model=dict)
async def route_register(data: RegisterReq):
  try:
    user = await db.users.find_unique(where={"username": data.username})
    if user:
      raise err.username_occupied
    
    new_user_data = {
      "username": data.username,
      "password": helpers.get_hashed_password(data.password),
    }
    new_user = await db.users.create(new_user_data)
    return {"id": new_user.id, "username": new_user.username}
  except Exception as e:
    logging.error(f"Exception raised while registering user: {e}")
    raise err.internal_error


@router.post("/login")
async def route_login(login_data: OAuth2PasswordRequestForm = Depends()):
  user = await db.users.find_unique(where={"username": login_data.username})
  if not user:
    raise err.credentials_exception
  if not helpers.verify_password(login_data.password, user.password):
    raise err.credentials_exception
  try:
    access_token = helpers.generate_access_token(user.id, user.username)
    refresh_token = helpers.generate_refresh_token(user.id, user.username)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
  except Exception as e:
    logging.error(f"Exception raised while logging in user: {e}")
    raise err.internal_error

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

# def get_password_hash(password: str):
#   return sha256(password.encode()).hexdigest()


# def is_valid_username(username: str):
#   if len(username) > 32:
#     raise err.username_too_long_exception
#   if len(username) < 4:
#     raise err.username_too_short_exception
#   user = sql.query(User.username).filter_by(username = username).first()
#   if user:
#     raise err.username_occupied
#   return True


# def verify_user(username: str, password: str):
#   user = sql.query(User).filter_by(username = username).first()
#   if user and user.password == sha256(password.encode()).hexdigest():
#     return user


# def add_user(username: str, password: str):
#   if is_valid_username(username):
#     hashed_password = get_password_hash(password)
#     user = User(username, hashed_password)
#     sql.add(user)
#     sql.commit()


# def create_jwt_token(data: dict):
#   to_encode = data.copy()
#   expire = datetime.utcnow() + timedelta(minutes=60)
#   to_encode.update({"exp": expire})
#   encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
#   return encoded_jwt


# def authenticate_user(username: str, password: str):
#   try:
#     user = verify_user(username, password)
#     if not user:
#       raise credentials_exception
    
#     token_data = {"sub": user.username, "id": user.id}
#     access_token = create_jwt_token(token_data)
#     return {"access_token": access_token, "token_type": "bearer"}
#   except:
#     raise internal_error


# def verify_user_auth(token: str = Depends(oauth2_scheme)) -> AuthData:
#   try:
#     payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256",])
#     username: str = payload.get("user")
#     if username is None:
#       raise credentials_exception
#     return payload
#   except jwt.DecodeError:
#     logging.error(f"Exception raised while decoding JWT.")
#     raise internal_error

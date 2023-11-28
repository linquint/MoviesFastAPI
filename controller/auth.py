from hashlib import sha256
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from interfaces.auth import AuthData
from models.database import sql
from models.model import User
from datetime import datetime, timedelta


SECRET_KEY = "1daf55137198005e896863a8951e5cc57bee1686ee0a34ae697e4ede1c5e8734"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


credentials_exception = HTTPException(
  status_code=status.HTTP_401_UNAUTHORIZED,
  detail="Could not validate credentials",
  headers={"WWW-Authenticate": "Bearer"},
)

username_too_long_exception = HTTPException(
  status_code=status.HTTP_400_BAD_REQUEST,
  detail="Username too long.",
)

username_too_short_exception = HTTPException(
  status_code=status.HTTP_400_BAD_REQUEST,
  detail="Username too short.",
)

username_occupied = HTTPException(
  status_code=status.HTTP_409_CONFLICT,
  detail="Username already exists.",
)

internal_error = HTTPException(
  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
  detail="Task failed successfully",
)


def get_password_hash(password: str):
  return sha256(password.encode()).hexdigest()


def is_valid_username(username: str):
  if len(username) > 32:
    raise username_too_long_exception
  if len(username) < 4:
    raise username_too_short_exception
  user = sql.query(User.username).filter_by(username = username).first()
  if user:
    raise username_occupied
  return True


def verify_user(username: str, password: str):
  user = sql.query(User).filter_by(username = username).first()
  if user and user.password == sha256(password.encode()).hexdigest():
    return user


def add_user(username: str, password: str):
  if is_valid_username(username):
    hashed_password = get_password_hash(password)
    user = User(username, hashed_password)
    sql.add(user)
    sql.commit()


def create_jwt_token(data: dict):
  to_encode = data.copy()
  expire = datetime.utcnow() + timedelta(minutes=60)
  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
  return encoded_jwt


def authenticate_user(username: str, password: str):
  try:
    user = verify_user(username, password)
    if not user:
      raise credentials_exception
    
    token_data = {"sub": user.username, "id": user.id}
    access_token = create_jwt_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}
  except:
    raise internal_error


def verify_user_auth(token: str = Depends(oauth2_scheme)) -> AuthData:
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256",])
    username: str = payload.get("user")
    if username is None:
      raise credentials_exception
    return payload
  except jwt.DecodeError:
    logging.error(f"Exception raised while decoding JWT.")
    raise internal_error

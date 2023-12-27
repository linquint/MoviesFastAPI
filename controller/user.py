import logging
from typing import Any
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from interfaces.auth import RefreshReq, RegisterReq, LoginResponse
from utils.deps import get_current_user
import utils.err as err
import utils.helpers as helpers
from db.prisma import prisma as db


router = APIRouter(
  prefix="/api",
  tags=["auth"],
)


@router.post("/register", response_model=dict)
async def route_register(data: RegisterReq):
  if not data.password.__eq__(data.passwordVerify):
    raise err.passwords_dont_match
  user = await db.users.find_unique(where={"username": data.username})
  if user:
    raise err.username_occupied
  
  new_user_data = {
    "username": data.username,
    "password": helpers.get_hashed_password(data.password),
  }
  new_user = await db.users.create(new_user_data)
  return {"id": new_user.id, "username": new_user.username}


@router.post("/login")
async def route_login(login_data: OAuth2PasswordRequestForm = Depends()) -> LoginResponse:
  user = await db.users.find_unique(where={"username": login_data.username})
  if not user:
    raise err.credentials_exception
  if not helpers.verify_password(login_data.password, user.password):
    raise err.credentials_exception
  try:
    access_token = helpers.generate_access_token(user.id, user.username)
    refresh_token = helpers.generate_refresh_token(user.id, user.username)
    return {
      "access_token": access_token,
      "refresh_token": refresh_token,
      "user": {
        "id": user.id,
        "username": user.username,
      }
    }
  except Exception as e:
    logging.error(f"Exception raised while logging in user: {e}")
    raise err.internal_error
  
  
@router.post("/refresh")
async def route_refresh(refresh: RefreshReq):
  try:
    payload = jwt.decode(refresh.refresh_token, helpers.dot_env("refresh"), algorithms=["HS256"])
    user = await db.users.find_unique(where={"username": payload.get("sub")})
    if not user:
      raise err.credentials_exception
    access_token = helpers.generate_access_token(user.id, user.username)
    return {
      "access_token": access_token,
      "user": {
        "id": user.id,
        "username": user.username,
      }
    }
  except Exception as e:
    logging.error(f"Exception raised while refreshing token: {e}")
    raise err.internal_error
  
  
@router.get("/likes")
async def route_user_likes(user: Any = Depends(get_current_user)):
  if not user:
    return []
  logging.info(f"Getting liked movies for user {user.id}")
  movies = await db.liked_movie.find_many(where={"userID": user.id}, include={"movies": True})
  return {"likes": [movie.movies.imdbID for movie in movies]}


@router.get("/recommendations")
async def route_recommendations(user: Any = Depends(get_current_user)):
  logging.info(f"Getting recommendations for user {user.id}")
  liked_movies_count = await db.liked_movie.count(where={"userID": user.id})
  if liked_movies_count < 5:
    raise err.not_enough_liked_movies
  
  liked_movies_rel = await db.liked_movie.find_many(where={"userID": user.id}, include={"movies": True})
  liked_movies = [movie.movies.title for movie in liked_movies_rel]
  liked_keywords_res = await db.query_raw(
    """
    SELECT DISTINCT COUNT(k.word) AS `count`, k.word AS word, mk.keywordID AS kw_id
    FROM liked_movie lm
    INNER JOIN movie_keyword mk ON mk.movieID = lm.movieID
    INNER JOIN keywords k ON k.id = mk.keywordID
    WHERE lm.userID = ?
    GROUP BY kw_id
    HAVING `count` > 1;
    """,
    user.id
  )
  liked_keywords: list[str] = [keyword["word"] for keyword in liked_keywords_res]
  liked_keywords_ids: list[str] = [str(keyword["kw_id"]) for keyword in liked_keywords_res]
  for lm in liked_movies:
    title_words = lm.lower().split(" ")
    for word in title_words:
      if word not in liked_keywords:
        liked_keywords.append(word)
  
  potential_movies_res = await db.query_raw(
    """
    SELECT DISTINCT m.title AS title, mk.movieID AS movie, k.word AS keyword
    FROM movie_keyword mk
    INNER JOIN keywords k ON k.id = mk.keywordID
    INNER JOIN movies m ON m.id = mk.keywordID
    WHERE mk.movieID IN (
        SELECT DISTINCT movieID
        FROM movie_keyword
        WHERE keywordID IN (?)
    )
    AND mk.movieID NOT IN (
      SELECT m.movieID FROM liked_movie m WHERE m.userID = ?
    );
    """,
    ",".join(liked_keywords_ids),
    user.id,
  )
  
  potential_movies = {}
  for movie in potential_movies_res:
    name = movie["movie"]
    if name in potential_movies:
      potential_movies[name].append(movie["keyword"])
    else:
      potential_movies[name] = [movie["keyword"]]
  
  movies_sim = {}
  for movie in potential_movies:
    keywords = potential_movies[movie]
    title = [pot["title"] for pot in potential_movies_res if pot["movie"] == movie][0].lower()
    keywords.extend([word for word in title.split(" ")])
    if len(keywords) > 1:
      movies_sim[movie] = helpers.jaccard_similarity(liked_keywords, keywords)
  
  movies_sorted = dict(sorted(movies_sim.items(), key=lambda item: item[1], reverse=True))
  
  print(movies_sorted)
  
  movies_ids = list(movies_sorted.keys())[:12]
  movies_res = await db.movies.find_many(where={"id": {"in": movies_ids}})
  movies = []
  for id in movies_ids:
    for movie in movies_res:
      if movie.id == id:
        movies.append(movie)
        break
  return {"recommendations": movies}


@router.get("/profile")
async def route_profile(user: Any = Depends(get_current_user)):
  logging.info(f"Getting profile for user {user.id}")
  liked_movies = await db.liked_movie.find_many(where={"userID": user.id}, include={"movies": True})
  liked_keywords = await db.query_raw(
    """
    SELECT k.word AS word, count(k.word) as total
    FROM liked_movie lm
    INNER JOIN movie_keyword mk ON mk.movieID = lm.movieID
    INNER JOIN keywords k ON k.id = mk.keywordID
    WHERE lm.userID = ?
    GROUP BY word
    ORDER BY total DESC
    LIMIT 20;
    """,
    user.id
  )
  movies = [movie.movies for movie in liked_movies]
  return {
    "movies": movies,
    "keywords": liked_keywords
  }

import logging
from typing import Any
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from interfaces.auth import RegisterReq
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


@router.get("/recommendations")
async def route_recommendations(user: Any = Depends(get_current_user)):
  logging.info(f"Getting recommendations for user {user.id}")
  liked_movies_count = await db.liked_movie.count(where={"userID": user.id})
  if liked_movies_count < 5:
    raise err.not_enough_liked_movies
  
  liked_keywords_res = await db.query_raw(
    """
    SELECT DISTINCT k.word AS word, mk.keywordID AS kw_id
    FROM liked_movie lm
    INNER JOIN movie_keyword mk ON mk.movieID = lm.movieID
    INNER JOIN keywords k ON k.id = mk.keywordID
    WHERE lm.userID = ?;
    """,
    user.id
  )
  liked_keywords: list[str] = [keyword["word"] for keyword in liked_keywords_res]
  liked_keywords_ids: list[str] = [str(keyword["kw_id"]) for keyword in liked_keywords_res]
  
  potential_movies_res = await db.query_raw(
    """
    SELECT DISTINCT mk.movieID AS movie, k.word AS keyword
    FROM movie_keyword mk
    INNER JOIN keywords k ON k.id = mk.keywordID
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
    if len(keywords) > 1:
      movies_sim[movie] = helpers.jaccard_similarity(liked_keywords, keywords)
  
  movies_sorted = dict(sorted(movies_sim.items(), key=lambda item: item[1], reverse=True))
  movies_ids = list(movies_sorted.keys())[:12]
  movies_res = await db.movies.find_many(where={"id": {"in": movies_ids}})
  movies = []
  for id in movies_ids:
    for movie in movies_res:
      if movie.id == id:
        movies.append(movie)
        break
  return movies

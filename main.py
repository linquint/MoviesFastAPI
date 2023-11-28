import json
import logging
import re
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

import config
from controller.auth import add_user, authenticate_user, get_password_hash, is_valid_username, verify_user_auth
from controller.home import movie_search, landing_keywords
from controller.movies import movie_details, movie_reviews, get_top_movies, add_movie_to_liked
from interfaces.auth import AuthData, LoginReq
from models.database import engine
from models.model import metadata_obj
import nltk

from services.db import add_movie_to_liked, get_random_movies, get_random_keywords, get_keywords_ilike, get_movies_by_keywords
from static.vectors import init_vectors
from static.words import init_word_lists

sentry_sdk.init(
  dsn="https://c32658a30102994242ba8b2ce119e541@o1136798.ingest.sentry.io/4506101713731584",
  # Set traces_sample_rate to 1.0 to capture 100%
  # of transactions for performance monitoring.
  traces_sample_rate=1.0,
  # Set profiles_sample_rate to 1.0 to profile 100%
  # of sampled transactions.
  # We recommend adjusting this value in production.
  profiles_sample_rate=1.0,
  integrations=[
    LoggingIntegration(
      level=logging.INFO,
      event_level=logging.ERROR
    )
  ]
)

app = FastAPI()

ALGORITHM = "HS256"

origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://linquint.dev",
    "http://192.168.1.237:5173",
    "https://movies.linquint.dev",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@lru_cache()
def get_settings():
    return config.Settings()


@app.on_event("startup")
async def init_db():
    print("Initializing database")
    metadata_obj.create_all(bind=engine)

    print("Initializing GloVe6B")
    init_vectors()
    init_word_lists()

    print("Initializing nltk")
    nltk.download('punkt')
    nltk.download('stopwords')

    if get_settings().dev:
        print("Development")
    else:
        print("Production")
        print("Initializing Top movies")
        # movies_res = await get_top_movies()
        # movies = json.loads(movies_res.decode("utf-8"))['results']
        # for movie in movies:
        #     imdb = re.findall("tt\d{7,8}", movie['url'])[0]
        #     if get_movie_by_imdb_id(imdb) is None:
        #         print(f"Adding {imdb}")
        #         await get_movie(imdb)
        #         await movie_reviews(imdb)
        # print("Initializing currently Most Popular movies")
        # IMDB chart ID: moviemeter
        print("Finished initializing movies")


@app.get("/api/search")
async def search_movie(q: str = Query(None), p: int = Query(1)):
    if type(q) is None or len(q) < 3:
        return {"response": [], "page": 0, "totalResults": 0}
    if p > 100:
        p = 1
    q = q.replace(' ', '%20')
    data = await movie_search(q, p)
    if data:
        return {"q": q, "page": p, "totalResults": data["count"], "response": json.loads(data["search"])}
    return {"response": [], "page": 0, "totalResults": 0}


@app.get("/api/movie/{imdb_id}/like")
async def like_movie(imdb_id: str, token: AuthData = Depends(verify_user_auth)):
  add_movie_to_liked(token.id, imdb_id)
  return {"response": "Movie added to liked"}


@app.get("/api/movie/{imdb_id}")
async def get_movie(imdb_id: str):
    if re.search("^tt\d{7,8}$", imdb_id) is None:
        return {"response": False}
    data = await movie_details(imdb_id)
    return {"id": imdb_id, "response": data}


@app.get("/api/reviews/{imdb_id}")
async def get_reviews(imdb_id: str):
    if re.search("^tt\d{7,8}$", imdb_id) is None:
        return {"response": False}
    data = await movie_reviews(imdb_id)
    return {"id": imdb_id, "response": data}


@app.get("/api/landing")
async def get_landing_page():
    keywords = landing_keywords()
    movies = get_random_movies(12)
    return {"keywords": keywords, "movies": movies}


@app.get("/api/keywords/autocomplete")
async def get_keywords_autocomplete(query: str = Query('')):
    if query == '':
        return {"response": get_random_keywords(20), "count": 20}
    data = get_keywords_ilike(query)
    count = len(data)
    return {"response": data, "count": count}


# TODO: Add pagination and limit to either 12 or 24 movies per page
@app.get("/api/keywords")
async def get_movies_filtered_by_keyword(keywords: str = Query(''), p: int = Query(1)):
    if keywords == '' or len(keywords) < 2:
        return {"response": False}
    try:
        return {"response": get_movies_by_keywords(keywords, p)}
    except Exception as e:
        print(f'Exception while getting movies by keywords. Keywords: {keywords}\nError: {e}')
        return {"response": False}


@app.post("/api/register", response_model=dict)
async def register_user(req: LoginReq):
  if not req.username or not req.password:
    logging.info(f"Register missing username or password.")
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Missing username or password."
    )
  add_user(req.username, req.password)
  logging.info(f"User {req.username} created successfully.")
  return {"response": "User created successfully."}


@app.post("/api/login")
async def login_user(req: OAuth2PasswordRequestForm = Depends()):
  if not req.username or not req.password:
    logging.info(f"Login missing username or password.")
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Missing username or password."
    )
  token = authenticate_user(req.username, req.password)
  logging.info(f"User {req.username} logged in successfully.")
  return token

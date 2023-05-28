import json
import re
import uvicorn

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from controller.home import movie_search, landing_keywords
from controller.movies import movie_details, movie_reviews, get_top_movies, get_movie_by_imdb_id
from models.database import engine
from models.model import metadata_obj
import nltk

from services.db import get_random_movies
from static.vectors import init_vectors
from static.words import init_word_lists

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://linquint.dev",
    "http://192.168.1.237:5173",
    "https://reviews.linquint.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


def run_server():
    uvicorn.run(app)


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

    print("Initializing Top movies")
    movies_res = await get_top_movies()
    movies = json.loads(movies_res.decode("utf-8"))['results']
    for movie in movies:
        imdb = re.findall("tt\d{7,8}", movie['url'])[0]
        if get_movie_by_imdb_id(imdb) is None:
            print(f"Adding {imdb}")
            await get_movie(imdb)
            await movie_reviews(imdb)
    print("Finished initializing top movies")


@app.get("/api/search")
async def search_movie(q: str = Query(None), p: int = Query(1)):
    if type(q) is None:
        return {"response": [], "page": 0, "totalResults": 0}
    if type(p) != "number" or p > 100:
        p = 1
    data = await movie_search(q, p)
    if data:
        return {"q": q, "page": p, "totalResults": data["count"], "response": json.loads(data["search"])}
    return {"response": [], "page": 0, "totalResults": 0}


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


@app.get("/api/keywords")
async def get_movies_by_keywords(list: str = Query('')):
    if list == '':
        return {"response": False}

import http.client
import json

from fastapi import HTTPException, status
from main import like_movie
from models.model import Movie, User

from services.db import get_movie_by_imdb_id, insert_movie, get_reviews_by_imdb_id, insert_reviews_keywords, \
    get_movie_data_by_imdb_id
from services.db import add_movie_to_liked as db_liked_movie
from services.extractor import retrieve_keywords
from services.scraper import scrape
from models.database import sql

headersDOJO = {
    'X-RapidAPI-Key': "3c28855955msh03796e646142a63p14bc99jsne913e6e6b778",
    'X-RapidAPI-Host': "online-movie-database.p.rapidapi.com"
}
headersCharts = {
    'X-RapidAPI-Key': "3c28855955msh03796e646142a63p14bc99jsne913e6e6b778",
    'X-RapidAPI-Host': "imdb-charts.p.rapidapi.com"
}


async def movie_details(imdb_id):
    movie = get_movie_by_imdb_id(imdb_id)
    if movie is None:
        conn = http.client.HTTPConnection("omdbapi.com")
        url = f"/?apikey=d49b3253&type=movie&plot=full&i={imdb_id}".replace(" ", "%20")
        conn.request("GET", url)
        res_data = conn.getresponse().read()
        conn.close()
        insert_movie(res_data)
    return get_movie_data_by_imdb_id(imdb_id)


async def movie_reviews(imdb_id, retry=0):
    reviews = get_reviews_by_imdb_id(imdb_id)
    if reviews is None or len(reviews) < 15:
        objs = json.loads(scrape(imdb_id))
        reviews_list = [r['content'] for r in objs]
        if len(reviews_list) == 0:
            if retry < 3:
                return await movie_reviews(imdb_id, retry + 1)
            else:
                return None
        else:
            keywords = retrieve_keywords(reviews_list)
            insert_reviews_keywords(imdb_id, objs, keywords)
    return get_movie_data_by_imdb_id(imdb_id)
    

async def get_top_movies():
    conn = http.client.HTTPSConnection("imdb-charts.p.rapidapi.com")
    conn.request("GET", "/charts?id=top-english-movies", headers=headersCharts)
    res = conn.getresponse()
    data = res.read()
    conn.close()
    return data


async def add_movie_to_liked(user: int, movie: str):
  db_liked_movie(user, movie)

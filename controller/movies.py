import http.client
import json
import logging
from typing import Annotated, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from interfaces.movies import SearchRes

from db.prisma import prisma as db
from utils import helpers
from utils.deps import get_current_user
from utils.vectors import keyword_avg

headersDOJO = {
    'X-RapidAPI-Key': "3c28855955msh03796e646142a63p14bc99jsne913e6e6b778",
    'X-RapidAPI-Host': "online-movie-database.p.rapidapi.com"
}
headersCharts = {
    'X-RapidAPI-Key': "3c28855955msh03796e646142a63p14bc99jsne913e6e6b778",
    'X-RapidAPI-Host': "imdb-charts.p.rapidapi.com"
}

router = APIRouter(
  prefix="/api",
  tags=["movies"],
)


@router.get("/search/{query}/{page}", tags=["search", "movies"])
async def route_search_movie(
  query: Annotated[str, Path(title="Search query")],
  page: Annotated[int, Path(title="Page number")],
) -> SearchRes:
  # Check if query is valid
  if len(query) < 3:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Search query too short."
    )
  # Get search results from OMDB API
  conn = http.client.HTTPConnection("omdbapi.com")
  url = f"/?apikey=d49b3253&type=movie&plot=full&s={query}&page={page}".replace(" ", "%20")
  conn.request("GET", url)
  conn_res = conn.getresponse().read()
  conn.close()
  omdb_res = json.loads(conn_res.decode("utf-8"))
  # Fetch results
  if "Search" in omdb_res:
    search_results = omdb_res["Search"]
    return {
      "query": query,
      "page": page,
      "count": int(omdb_res["totalResults"]),
      "search": [{
        "title": item["Title"],
        "releaseYear": item["Year"],
        "imdbID": item["imdbID"],
        "type": item["Type"],
        "poster": item["Poster"],
      } for item in search_results]
    }
  # No results found
  raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="No results found."
  )


@router.get("/movie/{imdb_id}", tags=["movies"])
async def route_get_movie(
  imdb_id: Annotated[str, Path(title="IMDB ID")],
):
  movie = await db.movies.find_first(where={"imdbID": imdb_id})
  logging.info(f"Get movie {imdb_id}. Movie found in database: {not not movie}")
  
  if not movie:
    # If movie is not in database, fetch it from OMDB API
    conn = http.client.HTTPConnection("omdbapi.com")
    url = f"/?apikey=d49b3253&type=movie&plot=full&i={imdb_id}".replace(" ", "%20")
    conn.request("GET", url)
    res_data = conn.getresponse().read()
    conn.close()
    
    # Scrape movie reviews from IMDB
    reviews_json = json.loads(await helpers.scrape(imdb_id))
    reviews = [review for review in reviews_json if review['content'] != '']
    keywords = helpers.retrieve_keywords(reviews)
    
    # Prepare movie data
    movie_obj = json.loads(res_data.decode('utf-8'))
    
    # Insert movie and create and link reviews and keywords with many-to-many relationship into database
    movie = await db.movies.create({
      "title": helpers.get_value(movie_obj, "Title"),
      "poster": helpers.get_value(movie_obj, "Poster"),
      "releaseYear": helpers.get_value(movie_obj, "Year", "int"),
      "runtime": helpers.get_value(movie_obj, "Runtime", "int", 0, " min"),
      "plot": helpers.get_value(movie_obj, "Plot"),
      "awards": helpers.get_value(movie_obj, "Awards"),
      "ratingIMDB": helpers.get_value(movie_obj, "imdbRating", "float"),
      "imdbVotes": helpers.get_value(movie_obj, "imdbVotes", "int", 0, ","),
      "imdbID": helpers.get_value(movie_obj, "imdbID"),
      "type": helpers.get_value(movie_obj, "Type"),
      "actors": helpers.get_value(movie_obj, "Actors", altvalue=""),
      "directors": helpers.get_value(movie_obj, "Director", altvalue=""),
      "genres": helpers.get_value(movie_obj, "Genre", altvalue=""),
      "movie_review": {
        "create": [
          {
            "reviews": {
              "create": {
                "author": helpers.get_value(review, 'author'),
                "rating": helpers.get_value(review, 'rating', 'int'),
                "helpfulness": helpers.get_value(review, 'helpfulness', 'float'),
                "upvotes": helpers.get_value(review, 'upvotes', 'int'),
                "downvotes": helpers.get_value(review, 'downvotes', 'int'),
                "title": helpers.get_value(review, "title"),
                "content": helpers.get_value(review, "content"),
                "spoilers": helpers.get_value(review, 'spoilers', 'bool'),
                "submittedOn": datetime.strptime(review['submittedOn'], "%d %B %Y"),
                "imdbID": imdb_id
              }
            }
          } for review in reviews
        ]
      },
      "movie_keyword": {
        "create": [
          {
            "keywords": {
              "connectOrCreate": {
                "where": {
                  "word": keyword
                },
                "create": {
                  "word": keyword
                }
              }
            }
          } for keyword in keywords
        ]
      }
    })
  movie_res = json.loads(movie.json())
  reviews = await db.reviews.find_many(where={"imdbID": imdb_id})
  keywords_rel = await db.movie_keyword.find_many(where={"movieID": movie.id}, include={"keywords": True})
  keywords = [keyword.keywords.word for keyword in keywords_rel]
  movie_res["reviews"] = reviews
  movie_res["keywords"] = keywords
  return movie_res


@router.get("/keywords/{page}")
async def route_movie_by_keywords(
  page: Annotated[int, Path(title="Page number")],
  keywords: Annotated[list[str], Query(title="Keywords", min_length=1)],
):
  return await db.movies.find_many(
    where={
      "movie_keyword": {
        "some": {
          "keywords": {
            "word": {
              "in": keywords
            }
          }
        }
      }
    },
    skip=(page - 1) * 12,
    take=12
  )


@router.get("/movies/like/{imdb_id}")
async def route_like_movie(
  imdb_id: Annotated[str, Path(title="IMDB ID")],
  user: Any = Depends(get_current_user)
):
  movie = await db.movies.find_first(where={"imdbID": imdb_id})
  is_liked = await db.liked_movie.find_first(where={"AND": [
    {"movieID": movie.id},
    {"userID": user.id}
  ]})
  if is_liked:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Movie already liked."
    )
  logging.info(f"Adding movie {imdb_id} to liked for user {user.id}")
  await db.liked_movie.create({
    "users": {
      "connect": {
        "id": user.id
      }
    },
    "movies": {
      "connect": {
        "id": movie.id
      }
    }
  })
  movies = await db.liked_movie.find_many(where={"userID": user.id}, include={"movies": True})
  return {"likes": [movie.movies.imdbID for movie in movies]}


@router.get("/movies/dislike/{imdb_id}")
async def route_dislike_movie(
  imdb_id: Annotated[str, Path(title="IMDB ID")],
  user: Any = Depends(get_current_user)
):
  logging.info(f"Removing movie {imdb_id} from liked for user {user.id}")
  movie = await db.movies.find_first(where={"imdbID": imdb_id})
  await db.liked_movie.delete(where={
    "movieID_userID": {
      "movieID": movie.id,
      "userID": user.id
    }
  })
  movies = await db.liked_movie.find_many(where={"userID": user.id}, include={"movies": True})
  return {"likes": [movie.movies.imdbID for movie in movies]}

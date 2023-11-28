import json
from fastapi import HTTPException, status

from sqlalchemy import func, text
from sqlalchemy.orm import joinedload
from main import like_movie

from models.database import sql
from models.model import Movie, Actor, Genre, Director, Review, Keyword, User

from datetime import datetime


def remove_non_ascii(s):
    return "".join(c for c in s if ord(c) < 128)


def get_value(data, key, vartype="str", altvalue=None, replacements=None):
    if key in data:
        if data[key] != "N/A":
            if replacements is not None:
                data[key] = data[key].replace(replacements, "")

            if vartype == 'int':
                return int(data[key])
            else:
                if vartype == 'float':
                    return float(data[key])
                else:
                    if vartype == 'bool':
                        return bool(data[key])
                    else:
                        return remove_non_ascii(data[key])
    return altvalue


def get_movie_by_imdb_id(imdbid):
    return sql.query(Movie).filter_by(imdbID=imdbid).first()


def get_reviews_by_imdb_id(imdbid):
    return sql.query(Review).filter_by(imdbID=imdbid).all()


def get_random_keywords(count):
    return sql.query(Keyword).order_by(func.random()).limit(count).all()


def get_random_movies(count):
    return sql.query(Movie).order_by(func.random()).limit(count).all()


def get_keywords_ilike(string: str):
    return sql.query(Keyword).filter(func.lower(Keyword.word).contains(string.lower())).all()


def get_top_keywords():
    results = sql.execute(text("""
        SELECT k.word, COUNT(*) AS occ 
        FROM movie_keyword 
        JOIN keywords k on movie_keyword.keywordID = k.id 
        GROUP BY k.id 
        ORDER BY occ DESC 
        LIMIT 20
    """))
    return json.dumps([{"word": row[0], "count": row[1]} for row in results.fetchall()])


def get_movies_by_keywords(kws_str: str, page: int):
    kws = kws_str.split(',')
    count = len(kws)
    start = (page - 1) * 12

    return sql.query(Movie) \
        .join(Movie.keywords) \
        .filter(Keyword.word.in_(kws)) \
        .group_by(Movie.id) \
        .having(func.count(Keyword.word) == count) \
        .offset(start) \
        .limit(12).all()


def get_movie_data_by_imdb_id(imdbid: str):
    return sql.query(Movie).options(
        joinedload(Movie.actors),
        joinedload(Movie.directors),
        joinedload(Movie.genres),
        joinedload(Movie.reviews),
        joinedload(Movie.keywords)
    ).filter(Movie.imdbID == imdbid).one()


def insert_movie(movie_data):
    movie_obj = json.loads(movie_data.decode('utf-8'))

    if len(movie_obj["Ratings"]) > 1:
        if movie_obj["Ratings"][1]['Source'] == "Rotten Tomatoes":
            rt = int(movie_obj["Ratings"][1]["Value"].replace('%', ''))
        else:
            rt = None
    else:
        rt = None

    movie = Movie(
        title=movie_obj['Title'],
        poster=movie_obj['Poster'],
        releaseYear=get_value(movie_obj, "Year", "int"),
        runtime=get_value(movie_obj, "Runtime", "int", 0, " min"),
        plot=get_value(movie_obj, "Plot"),
        awards=get_value(movie_obj, "Awards"),
        ratingIMDB=get_value(movie_obj, "imdbRating", "float"),
        ratingRT=rt,
        ratingMETA=get_value(movie_obj, "Metascore", "int"),
        imdbVotes=get_value(movie_obj, "imdbVotes", "int", 0, ","),
        imdbID=get_value(movie_obj, "imdbID"),
        type=get_value(movie_obj, "Type")
    )
    actors = movie_obj["Actors"].split(", ")
    genres = movie_obj["Genre"].split(", ")
    directors = movie_obj["Director"].split(", ")

    sql.add(movie)
    for a in actors:
        actor = Actor(actorName=a)
        sql.add(actor)
        movie.actors.append(actor)
    for g in genres:
        genre = Genre(genreName=g)
        sql.add(genre)
        movie.genres.append(genre)
    for d in directors:
        director = Director(directorName=d)
        sql.add(director)
        movie.directors.append(director)
    sql.commit()


def does_keyword_exist(kw):
    return sql.query(Keyword).filter(Keyword.word == kw).first()


def insert_reviews_keywords(imdb_id, objs, keywords):
    movie = sql.query(Movie).filter(Movie.imdbID == imdb_id).first()
    
    for k in keywords:
        kw = does_keyword_exist(k)
        if not kw:
            kw = Keyword(word=k)
            sql.add(kw)
        movie.keywords.append(kw)

    for obj in objs:
        review = Review(
            author=get_value(obj, 'author'),
            rating=obj['rating'],
            helpfulness=obj['helpfulness'],
            upvotes=obj['upvotes'],
            downvotes=obj['downvotes'],
            title=get_value(obj, "title"),
            content=get_value(obj, "content"),
            spoilers=obj['spoilers'],
            submittedOn=datetime.strptime(obj['submittedOn'], "%d %B %Y"),
            imdbID=imdb_id
        )
        sql.add(review)
        movie.reviews.append(review)
    sql.commit()
    
    
async def add_movie_to_liked(user: int, movie: str):
  is_liked = sql.query(like_movie).filter_by(userID=user, movieID=movie)
  if is_liked is not None:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail="Movie is already liked.",
    )
  
  movie = sql.query(Movie).filter_by(imdbID=movie).first()
  user = sql.query(User).filter_by(id=user).first()
  if not user or not movie:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Movie or user not found."
    )
  
  movie.users.add(user)
  user.movies.add(movie)
  sql.commit()

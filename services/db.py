import json

from sqlalchemy import func, text
from sqlalchemy.orm import joinedload

from models.database import sql
from models.model import Movie, Actor, Genre, Director, Review, Summary, Keyword


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


def get_movies_by_keywords_array(kws: list, f: str, count: int):
    if f == 'and':
        return sql.query(Keyword)\
            .join(Keyword.movies)\
            .filter(Keyword.word.in_(kws))\
            .group_by(Movie.id)\
            .having(func.count(Keyword.word) == count) \
            .options(
                joinedload(Keyword.movies)
            ).all()
    else:
        return sql.query(Keyword).options(
            joinedload(Keyword.movies)
        ).filter(Keyword.word.in_(kws)).all()


def get_movie_data_by_imdb_id(imdbid):
    return sql.query(Movie).options(
        joinedload(Movie.actors),
        joinedload(Movie.directors),
        joinedload(Movie.genres),
        joinedload(Movie.reviews),
        joinedload(Movie.summary),
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


def insert_reviews_summary(imdb_id, objs, keywords, summary_spoilers, summary_clean=None):
    movie = sql.query(Movie).filter(Movie.imdbID == imdb_id).one()

    summary = Summary(contentClean=summary_clean, contentSpoilers=summary_spoilers)
    sql.add(summary)
    movie.summary = summary

    for k in keywords:
        kw = does_keyword_exist(k)
        if not kw:
            kw = Keyword(word=k)
            sql.add(kw)
        movie.keywords.append(kw)

    for obj in objs['reviews']:
        review = Review(
            author=obj['author']['displayName'],
            rating=get_value(obj, "authorRating", "int", 0),
            helpfulness=get_value(obj, "helpfulnessScore", "float"),
            upvotes=get_value(obj['interestingVotes'], "up", "int", 0),
            downvotes=get_value(obj['interestingVotes'], "down", "int", 0),
            title=get_value(obj, "reviewTitle"),
            content=get_value(obj, "reviewText"),
            spoilers=get_value(obj, "spoiler", "bool", False),
            submittedOn=get_value(obj, "submissionDate"),
            imdbID=imdb_id
        )
        sql.add(review)
        movie.reviews.append(review)
    sql.commit()

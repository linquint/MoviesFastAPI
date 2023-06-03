from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Float, DateTime, func, Boolean, Text, BigInteger, ForeignKey, Table
from sqlalchemy.orm import relationship, registry

mapper_registry = registry()
metadata_obj = mapper_registry.metadata


movie_keyword = Table(
    "movie_keyword",
    metadata_obj,
    Column("movieID", ForeignKey("movies.id"), primary_key=True),
    Column("keywordID", ForeignKey("keywords.id"), primary_key=True)
)

movie_review = Table(
    "movie_review",
    metadata_obj,
    Column("movieID", ForeignKey("movies.id"), primary_key=True),
    Column("reviewID", ForeignKey("reviews.id"), primary_key=True)
)

movie_actor = Table(
    "movie_actor",
    metadata_obj,
    Column("movieID", ForeignKey("movies.id"), primary_key=True),
    Column("actorID", ForeignKey("actors.id"), primary_key=True)
)

movie_genre = Table(
    "movie_genre",
    metadata_obj,
    Column("movieID", ForeignKey("movies.id"), primary_key=True),
    Column("genreID", ForeignKey("genres.id"), primary_key=True)
)

movie_director = Table(
    "movie_director",
    metadata_obj,
    Column("movieID", ForeignKey("movies.id"), primary_key=True),
    Column("directorID", ForeignKey("directors.id"), primary_key=True)
)


@mapper_registry.mapped
@dataclass
class Keyword:
    __table__ = Table(
        "keywords",
        metadata_obj,
        Column("id", BigInteger, primary_key=True, index=True),
        Column("word", String(255), unique=True),
    )
    word: str
    __mapper_args__ = {
        "properties": {
            "movies": relationship("Movie", secondary=movie_keyword, back_populates="keywords")
        }
    }


@mapper_registry.mapped
@dataclass
class Review:
    __table__ = Table(
        "reviews",
        metadata_obj,
        Column("id", Integer, primary_key=True, index=True),
        Column("imdbID", String(255)),
        Column("author", String(255)),
        Column("rating", Integer, nullable=True),
        Column("helpfulness", Float),
        Column("upvotes", Integer),
        Column("downvotes", Integer),
        Column("title", String(255)),
        Column("content", Text),
        Column("spoilers", Boolean),
        Column("submittedOn", DateTime),
    )
    imdbID: str
    author: str
    helpfulness: float
    upvotes: int
    downvotes: int
    title: str
    content: str
    spoilers: bool
    submittedOn: Optional[datetime] = datetime.now()
    rating: Optional[int] = None
    __mapper_args__ = {
        "properties": {
            "movies": relationship("Movie", secondary=movie_review, back_populates="reviews")
        }
    }


@mapper_registry.mapped
@dataclass
class Summary:
    __table__ = Table(
        "summaries",
        metadata_obj,
        Column("id", Integer, primary_key=True, index=True),
        Column("contentClean", Text),
    )
    contentClean: Optional[str] = None
    __mapper_args__ = {
        "properties": {
            "movie": relationship("Movie", back_populates="summary", uselist=False)
        }
    }


@mapper_registry.mapped
@dataclass
class Actor:
    __table__ = Table(
        "actors",
        metadata_obj,
        Column("id", Integer, primary_key=True, index=True),
        Column("actorName", String(255)),
    )
    actorName: str
    __mapper_args__ = {
        "properties": {
            "movies": relationship("Movie", secondary=movie_actor, back_populates="actors")
        }
    }


@mapper_registry.mapped
@dataclass
class Genre:
    __table__ = Table(
        "genres",
        metadata_obj,
        Column("id", Integer, primary_key=True, index=True),
        Column("genreName", String(255)),
    )
    genreName: str
    __mapper_args__ = {
        "properties": {
            "movies": relationship("Movie", secondary=movie_genre, back_populates="genres")
        }
    }


@mapper_registry.mapped
@dataclass
class Director:
    __table__ = Table(
        "directors",
        metadata_obj,
        Column("id", Integer, primary_key=True, index=True),
        Column("directorName", String(255)),
    )
    directorName: str
    __mapper_args__ = {
        "properties": {
            "movies": relationship("Movie", secondary=movie_director, back_populates="directors")
        }
    }


@mapper_registry.mapped
@dataclass
class Movie:
    __table__ = Table(
        "movies",
        metadata_obj,
        Column("id", Integer, primary_key=True, index=True),
        Column("title", String(255)),
        Column("poster", String(255), nullable=True),
        Column("releaseYear", Integer),
        Column("runtime", Integer),
        Column("plot", Text, nullable=True),
        Column("awards", String(255), nullable=True),
        Column("ratingIMDB", Float),
        Column("ratingRT", Float, nullable=True),
        Column("ratingMETA", Float, nullable=True),
        Column("imdbVotes", Integer),
        Column("imdbID", String(255)),
        Column("type", String(255)),
        Column("addedOn", DateTime, default=func.now()),
        Column("summary_id", Integer, ForeignKey("summaries.id"), nullable=True),
    )
    title: str
    releaseYear: int
    runtime: int
    ratingIMDB: float
    imdbVotes: int
    imdbID: str
    type: str
    addedOn: Optional[datetime] = datetime.now()
    poster: Optional[str] = None
    plot: Optional[str] = None
    awards: Optional[str] = None
    ratingRT: Optional[float] = None
    ratingMETA: Optional[float] = None
    summary: Optional[Summary] = field(default_factory=str)
    keywords: List[Keyword] = field(default_factory=list)
    reviews: List[Review] = field(default_factory=list)
    actors: List[Actor] = field(default_factory=list)
    genres: List[Genre] = field(default_factory=list)
    directors: List[Director] = field(default_factory=list)
    __mapper_args__ = {
        "properties": {
            "summary": relationship('Summary', back_populates="movie", uselist=False),
            "keywords": relationship("Keyword", secondary=movie_keyword, back_populates="movies"),
            "reviews": relationship("Review", secondary=movie_review, back_populates="movies"),
            "actors": relationship("Actor", secondary=movie_actor, back_populates="movies"),
            "genres": relationship("Genre", secondary=movie_genre, back_populates="movies"),
            "directors": relationship("Director", secondary=movie_director, back_populates="movies"),
        }
    }

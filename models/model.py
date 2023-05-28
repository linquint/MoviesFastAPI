from sqlalchemy import Column, Integer, String, Float, DateTime, func, Boolean, Text, BigInteger, ForeignKey, Table
from sqlalchemy.orm import relationship
from models.database import Base

metadata_obj = Base.metadata


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


class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(BigInteger, primary_key=True, index=True)
    word = Column(String(255), unique=True)
    movies = relationship("Movie", secondary=movie_keyword, back_populates="keywords")


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    imdbID = Column(String(255))
    author = Column(String(255))
    rating = Column(Integer, nullable=True)
    helpfulness = Column(Float)
    upvotes = Column(Integer)
    downvotes = Column(Integer)
    title = Column(String(255))
    content = Column(Text)
    spoilers = Column(Boolean)
    submittedOn = Column(DateTime)
    movies = relationship("Movie", secondary=movie_review, back_populates="reviews")


class Summary(Base):
    __tablename__ = "summaries"
    id = Column(Integer, primary_key=True, index=True)
    contentClean = Column(Text, nullable=True)
    contentSpoilers = Column(Text)
    movie = relationship("Movie", back_populates="summary", uselist=False)


class Actor(Base):
    __tablename__ = "actors"
    id = Column(Integer, primary_key=True, index=True)
    actorName = Column(String(255))
    movies = relationship("Movie", secondary=movie_actor, back_populates="actors")


class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True, index=True)
    genreName = Column(String(255))
    movies = relationship("Movie", secondary=movie_genre, back_populates="genres")


class Director(Base):
    __tablename__ = "directors"
    id = Column(Integer, primary_key=True, index=True)
    directorName = Column(String(255))
    movies = relationship("Movie", secondary=movie_director, back_populates="directors")


class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    poster = Column(String(255), nullable=True)
    releaseYear = Column(Integer)
    runtime = Column(Integer)
    plot = Column(Text, nullable=True)
    awards = Column(String(255), nullable=True)
    ratingIMDB = Column(Float)
    ratingRT = Column(Float, nullable=True)
    ratingMETA = Column(Float, nullable=True)
    imdbVotes = Column(Integer)
    imdbID = Column(String(255))
    type = Column(String(255))
    addedOn = Column(DateTime, default=func.now())
    summary_id = Column(Integer, ForeignKey("summaries.id"), nullable=True)
    summary = relationship('Summary', back_populates="movie", uselist=False)
    keywords = relationship("Keyword", secondary=movie_keyword, back_populates="movies")
    reviews = relationship("Review", secondary=movie_review, back_populates="movies")
    actors = relationship("Actor", secondary=movie_actor, back_populates="movies")
    genres = relationship("Genre", secondary=movie_genre, back_populates="movies")
    directors = relationship("Director", secondary=movie_director, back_populates="movies")

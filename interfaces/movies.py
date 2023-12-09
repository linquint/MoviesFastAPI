from pydantic import BaseModel


class SearchMovie(BaseModel):
  title: str
  releaseYear: str
  imdbID: str
  type: str
  poster: str


class SearchRes(BaseModel):
  query: str
  page: int
  count: int
  search: list[SearchMovie]

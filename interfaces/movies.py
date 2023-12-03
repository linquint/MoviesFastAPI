from pydantic import BaseModel


class SearchRes(BaseModel):
  query: str
  page: int
  count: int
  results: str

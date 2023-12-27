from typing import Annotated
from fastapi import APIRouter, Query
from db.prisma import prisma as db


router = APIRouter(
  prefix="/api",
  tags=["keywords"],
)


@router.get("/keywords/autocomplete")
async def route_keywords_autocomplete(
  query: Annotated[str, Query(title="Search query", max_length=32, min_length=2)],
):
  clean_query = query.strip().lower()
  if len(clean_query) < 2:
    return []
  keywords = await db.keywords.find_many(
    where={
      "word": {
        "contains": clean_query
      }
    }
  )
  return [{ "id": keyword.id, "word": keyword.word } for keyword in keywords]

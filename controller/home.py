from fastapi import APIRouter

from db.prisma import prisma as db


router = APIRouter(
  prefix="/api",
  tags=["home"],
)


@router.get("/home")
async def route_home():
  keywords_top = await db.query_raw(
    '''
    SELECT COUNT(MKW.keywordID) total, KW.word word
    FROM movie_keyword MKW
    INNER JOIN keywords KW ON KW.id = MKW.keywordID
    GROUP BY word
    ORDER BY total DESC
    LIMIT 20;
    '''
  )
  
  keywords_random = await db.query_raw(
    '''
    SELECT id, word
    FROM keywords
    ORDER BY RAND()
    LIMIT 20;
    '''
  )
  
  movies_random = await db.query_raw(
    '''
    SELECT *
    FROM movies
    WHERE title IS NOT NULL
    ORDER BY RAND()
    LIMIT 24;
    '''
  )
  return { "top": keywords_top, "random": keywords_random, "movies": movies_random }

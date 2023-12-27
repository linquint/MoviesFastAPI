import logging
from functools import lru_cache
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
import config
import nltk

from controller.movies import router as movies_router
from controller.home import router as home_router
from controller.keywords import router as keywords_router
from controller.user import router as user_router
from db.prisma import prisma as db

sentry_sdk.init(
  dsn="https://c32658a30102994242ba8b2ce119e541@o1136798.ingest.sentry.io/4506101713731584",
  # Set traces_sample_rate to 1.0 to capture 100%
  # of transactions for performance monitoring.
  traces_sample_rate=1.0,
  # Set profiles_sample_rate to 1.0 to profile 100%
  # of sampled transactions.
  # We recommend adjusting this value in production.
  profiles_sample_rate=1.0,
  integrations=[
    LoggingIntegration(
      level=logging.INFO,
      event_level=logging.ERROR
    )
  ]
)


ALGORITHM = "HS256"
ORIGINS = [
  "http://localhost",
  "http://localhost:5173",
  "https://linquint.dev",
  "http://192.168.1.237:5173",
  "http://192.168.1.253:5173",
  "https://movies.linquint.dev",
  "http://localhost:3000",
]

router = APIRouter(
  prefix="/api",
  include_in_schema=True,
  tags=["API"],
)

app = FastAPI()
app.add_middleware(
  CORSMiddleware,
  allow_origins=ORIGINS,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)
app.include_router(router=router)
app.include_router(router=home_router)
app.include_router(router=keywords_router)
app.include_router(router=movies_router)
app.include_router(router=user_router)


@lru_cache()
def get_settings():
  return config.Settings()


@app.on_event("startup")
async def init_db():
  logging.info("Initializing database")
  await db.connect()

  logging.info("Initializing NLTK")
  nltk.download('punkt')
  nltk.download('stopwords')
  nltk.download('averaged_perceptron_tagger')
  logging.info("Initialization complete")
  
  
@app.on_event("shutdown")
async def shutdown_db():
  logging.info("Shutting down database")
  await db.disconnect()


@router.get("/health")
async def health_check():
  return {"status": "ok"}

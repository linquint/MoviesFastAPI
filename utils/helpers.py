from datetime import datetime, timedelta
from functools import lru_cache
import json
import math
import re
import jwt
from passlib.context import CryptContext
from sklearn.feature_extraction.text import TfidfVectorizer

from bs4 import BeautifulSoup
import requests
import yake
import config
import nltk
from static.words import stopwords, adjectives


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30
ALGORITHM = "HS256"
PUNCTUATION = """!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""


@lru_cache()
def dot_env(key: str):
  env = config.Settings()
  if key == "refresh":
    return env.JWT_REFRESH_KEY
  return env.JWT_SECRET_KEY


def remove_non_ascii(s):
  return "".join(c for c in s if ord(c) < 128)


def get_value(data, key, vartype="str", altvalue=None, replacements=None):
  try:
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
  except:
    return altvalue
  return altvalue


async def scrape(title_id):
  url = f'https://www.imdb.com/title/{title_id}/reviews?sort=curated&dir=desc&ratingFilter=0'
  page = requests.get(url)

  soup = BeautifulSoup(page.content, "html.parser")
  lister = soup.find(class_="lister")
  lister_items = lister.find_all("div", class_="lister-item-content")
  reviews = []

  for item in lister_items:
    review = {
      "imdbID": title_id,
      "author": None,
      "rating": None,
      "helpfulness": 0,
      "upvotes": 0,
      "downvotes": 0,
      "title": "",
      "content": "",
      "spoilers": False,
      "submittedOn": "",
    }

    rating_div = item.find("span", class_="rating-other-user-rating")
    if rating_div is not None:
      rating = rating_div.find("span").text
      review['rating'] = int(rating)

    title: str = item.find("a", class_="title").text
    review['title'] = title.strip().replace("\n", "")

    author_span = item.find("span", class_="display-name-link")
    author = author_span.find("a").text
    review['author'] = author

    submitted_on = item.find("span", class_="review-date").text
    review['submittedOn'] = submitted_on

    content = item.find("div", class_="text").text
    review['content'] = content
    
    contains_spoiler = item.find("span", class_="spoiler-warning")
    review['spoilers'] = contains_spoiler is not None

    actions = item.find("div", class_="actions").text
    text = actions.replace(",", "")
    matched = re.findall(r"[0-9]+", text)
    if len(matched) == 2:
      upvotes = int(matched[0])
      total = int(matched[1])
      downvotes = total - upvotes
      helpfulness = upvotes / total
      review['upvotes'] = upvotes
      review['downvotes'] = downvotes
      review['helpfulness'] = helpfulness
    reviews.append(review)
  return json.dumps(reviews)


# def retrieve_keywords(reviews):
#   # valid_pos = ["JJ", "JJS", "RB", "PRP", "RBS", "VBG", "VB"]
#   invalid_pos = ['DT', 'VBZ', 'CD', 'POS', 'CC', 'PRP', 'IN', '.', 'PRP$', ',', 'NNP', 'NNS']
#   reviews_as_text = " ".join([review["content"] for review in reviews])
#   max_ngram_size = 3
#   deduplication_threshold = 0.9
#   deduplication_algorithm = 'seqm'
#   window_size = 2
#   keyword_count = 100
  
#   keyword_extractor = yake.KeywordExtractor(
#     lan="en",
#     n=max_ngram_size,
#     dedupLim=deduplication_threshold,
#     dedupFunc=deduplication_algorithm,
#     windowsSize=window_size,
#     top=keyword_count,
#   )
  
#   keywords = keyword_extractor.extract_keywords(reviews_as_text)
#   valid_keywords = []
#   for keyword in keywords:
#     tokenized_keyword = nltk.word_tokenize(keyword[0])
#     tagged_keyword = nltk.pos_tag(tokenized_keyword)
#     if any([tag[1] in invalid_pos for tag in tagged_keyword]) is False:
#       valid_keywords.append(keyword)
  
#   # tokenized_keywords = nltk.word_tokenize(" ".join([keyword[0] for keyword in keywords]))
#   # tagged_keywords = nltk.pos_tag(tokenized_keywords)
#   print(valid_keywords)
#   return keywords

def retrieve_keywords(reviews):
  reviews_text: list[str] = [review["content"] for review in reviews]
  tfidf_vectorizer = TfidfVectorizer(stop_words=stopwords)
  tfidf_matrix = tfidf_vectorizer.fit_transform(reviews_text)
  feature_names = tfidf_vectorizer.get_feature_names_out()
  
  keywords_combined = {}
  for i in range(len(reviews_text)):
    sorted_indices = tfidf_matrix[i].toarray().argsort()[0, ::-1]
    for j in range(25):
      keyword_index = sorted_indices[j]
      keyword = feature_names[keyword_index]
      tfidf_score = tfidf_matrix[i, keyword_index]
      if keyword in keywords_combined:
        keywords_combined[keyword].append(tfidf_score)
      else:
        keywords_combined[keyword] = [tfidf_score]
  keywords_scores = [(keyword, math.pow(len(scores) * math.exp(1), sum(scores))) for keyword, scores in keywords_combined.items()]
  keywords_scores.sort(key=lambda x: x[1], reverse=True)
  return [keyword[0] for keyword in keywords_scores if keyword[0] in adjectives]


def get_hashed_password(password: str) -> str:
  return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
  return password_context.verify(password, hashed_pass)


def generate_access_token(id, sub, expires: int = None) -> str:
  if not expires:
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  else:
    expires = datetime.utcnow() + expires
  to_encode = {"exp": expires, "sub": sub, "id": id}
  SECRET = dot_env("access")
  encoded_jwt = jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
  return encoded_jwt


def generate_refresh_token(id, sub, expires: int = None) -> str:
  if not expires:
    expires = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
  else:
    expires = datetime.utcnow() + expires
  to_encode = {"exp": expires, "sub": sub, "id": id}
  SECRET = dot_env("refresh")
  encoded_jwt = jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
  return encoded_jwt

import os.path

import numpy as np

vectors = {}


def init_vectors():
  script_dir = os.path.dirname(os.path.abspath(__file__))
  file_path = os.path.join(script_dir, '../static/glove.6B.50d.txt')
  f = open(file_path, encoding='utf-8')
  for line in f:
    values = line.split()
    word = values[0]
    coefs = np.asarray(values[1:], dtype='float32')
    vectors[word] = coefs
  f.close()


def keyword_avg(keywords: list[str]):
  if len(vectors) == 0:
    init_vectors()
  valid_keywords = [word for word in keywords if word in vectors]
  if valid_keywords is None or len(valid_keywords) == 0:
    return None
  valid_keywords = valid_keywords[:10]
  keywords_vectors = np.array([vectors[word] for word in valid_keywords])
  return np.mean(keywords_vectors, axis=0)

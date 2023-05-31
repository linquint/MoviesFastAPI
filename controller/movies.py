import http.client
import json
from collections import Counter

import nltk
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

from services.db import get_movie_by_imdb_id, insert_movie, get_reviews_by_imdb_id, insert_reviews_summary, \
    get_movie_data_by_imdb_id, get_movies_by_keywords_array
from static.vectors import vectors
from static.words import stopwords, adjectives

headersDOJO = {
    'X-RapidAPI-Key': "3c28855955msh03796e646142a63p14bc99jsne913e6e6b778",
    'X-RapidAPI-Host': "online-movie-database.p.rapidapi.com"
}
headersCharts = {
    'X-RapidAPI-Key': "3c28855955msh03796e646142a63p14bc99jsne913e6e6b778",
    'X-RapidAPI-Host': "imdb-charts.p.rapidapi.com"
}
PUNCTUATION = """!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""


async def movie_details(imdb_id):
    movie = get_movie_by_imdb_id(imdb_id)
    if movie is None:
        conn = http.client.HTTPConnection("omdbapi.com")
        url = f"/?apikey=d49b3253&type=movie&plot=full&i={imdb_id}".replace(" ", "%20")
        conn.request("GET", url)
        res_data = conn.getresponse().read()
        conn.close()
        insert_movie(res_data)
    return get_movie_data_by_imdb_id(imdb_id)


async def movie_reviews(imdb_id, retry=0):
    reviews = get_reviews_by_imdb_id(imdb_id)
    if reviews is None or len(reviews) < 15:
        conn_dojo = http.client.HTTPSConnection("online-movie-database.p.rapidapi.com")
        conn_dojo.request("GET", f"/title/get-user-reviews?tconst={imdb_id}", headers=headersDOJO)
        res_dojo = conn_dojo.getresponse()
        data = res_dojo.read()
        conn_dojo.close()
        objs = json.loads(data.decode('utf-8'))
        reviews_list = [r['reviewText'] for r in objs['reviews']]
        if len(reviews_list) < 10:
            if retry < 3:
                return await movie_reviews(imdb_id, retry + 1)
            else:
                return None
        else:
            keywords = retrieve_keywords(reviews_list)
            summary = retrieve_summary(reviews_list)
            summary_clean_text = [review['reviewText'] for review in objs['reviews'] if not review['spoiler']]
            if len(summary_clean_text) > 100:
                summary_clean = retrieve_summary()
                insert_reviews_summary(imdb_id, objs, keywords, summary, summary_clean)
            else:
                insert_reviews_summary(imdb_id, objs, keywords, summary)
    return get_movie_data_by_imdb_id(imdb_id)


def get_movies_from_keywords(kws_str: str, func: str):
    kws = kws_str.split(',')
    count = len(kws)
    return get_movies_by_keywords_array(kws, func, count)


def clean_text(text):
    text = text.lower()  # text to lower case
    return ''.join([c for c in text if c not in PUNCTUATION])  # remove punctuation


def sort_dic(matrix):
    tuples = zip(matrix.col, matrix.data)
    return sorted(tuples, key=lambda x: (x[1], x[0]), reverse=True)


def get_keywords(vectizer, feature_names, doc, top_kws=100):
    tf_idf_vector = vectizer.transform([doc])
    sorted_items = sort_dic(tf_idf_vector.tocoo())

    # get top n keywords
    sorted_items = sorted_items[:top_kws * 2]
    score_vals = []
    feature_vals = []

    # word index and corresponding tf-idf score
    for idx, score in sorted_items:
        score_vals.append(round(score, 3))
        feature_vals.append(feature_names[idx])

    results = {}
    for idx in range(len(feature_vals)):
        results[feature_vals[idx]] = score_vals[idx]
    return results


def extract_keywords(rws, vkw, fnames):
    top = []
    for rw in rws[0:]:
        k = get_keywords(vkw, fnames, rw)
        counter = Counter()
        counter.update(top)
        counter.update(k)
        kws = sorted(counter.items(), key=lambda x: x[1], reverse=True)
        top = list(dict(kws).keys())
    return top


def retrieve_keywords(content, sentence=None, count=25):
    keywords = []
    reviews = pd.Series(content).apply(clean_text).to_list()

    vectorizer = TfidfVectorizer(stop_words=stopwords, smooth_idf=True, use_idf=True)
    vectorizer.fit_transform(reviews)
    feature_names = vectorizer.get_feature_names_out()
    if sentence is None:
        tmp_keywords = extract_keywords(reviews, vectorizer, feature_names)
    else:
        tmp_keywords = extract_keywords(sentence, vectorizer, feature_names)

    for kw in tmp_keywords:
        adj = len(set((pd.Series(kw)).to_list()).intersection(adjectives)) > 0
        if not adj:
            continue
        keywords.append(kw)
        if len(keywords) >= count:
            break

    return keywords


def remove_stopwords(sentence, sws):
    new_sentence = " ".join([s for s in sentence if s not in sws])
    return new_sentence


def retrieve_summary(content):
    text_combined = ' '.join(content)
    sentences = nltk.sent_tokenize(text_combined)

    tmp_text = pd.Series(sentences).apply(clean_text).to_list()
    text = [remove_stopwords(r.split(), stopwords) for r in tmp_text]

    sentence_vectors = []
    for i in text:
        if len(i) != 0:
            v = sum([vectors.get(w, np.zeros((50,))) for w in i.split()]) / (len(i.split()) + 0.001)
        else:
            v = np.zeros((50,))
        sentence_vectors.append(v)

    similarity_matrix = np.zeros([len(sentences), len(sentences)])
    for i in range(len(sentences)):
        for j in range(len(sentences)):
            if i != j:
                similarity_matrix[i][j] = \
                    cosine_similarity(sentence_vectors[i].reshape(1, 50), sentence_vectors[j].reshape(1, 50))[0, 0]

    nx_graph = nx.from_numpy_array(similarity_matrix)
    try:
        scores = nx.pagerank(nx_graph, max_iter=500, tol=1.0e-4)
        ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
        summary = ''
        for i in range(10):
            summary += ranked_sentences[i][1]
        return summary
    except:
        print("Error occurred.")
        return None
    

async def get_top_movies():
    conn = http.client.HTTPSConnection("imdb-charts.p.rapidapi.com")
    conn.request("GET", "/charts?id=top-english-movies", headers=headersCharts)
    res = conn.getresponse()
    data = res.read()
    conn.close()
    return data

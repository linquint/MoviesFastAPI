from collections import Counter

import networkx as nx
import numpy as np
from networkx import PowerIterationFailedConvergence
from sklearn.metrics.pairwise import cosine_similarity

from static.vectors import vectors
from static.words import stopwords, adjectives

import nltk
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

PUNCTUATION = """!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""


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


def remove_stopwords(sentence, sws):
    new_sentence = " ".join([s for s in sentence if s not in sws])
    return new_sentence


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

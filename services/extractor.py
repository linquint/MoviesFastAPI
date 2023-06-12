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
        for i in range(25):
            summary += ranked_sentences[i][1] + ' '
            if len(summary) > 2600:
                break
        return summary
    except PowerIterationFailedConvergence as nxe:
        print(f"Pagerank error: {nxe}")
    except Exception as e:
        print(f"Other error: {e}")
    return None

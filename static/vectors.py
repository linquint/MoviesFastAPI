import os.path

import numpy as np

vectors = {}


def init_vectors():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'glove.6B.50d.txt')
    f = open(file_path, encoding='utf-8')
    for line in f:
        values = line.split()
        word = values[0]
        coefs = np.asarray(values[1:], dtype='float32')
        vectors[word] = coefs
    f.close()

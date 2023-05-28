import os


def open_text_file(filename: str):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    with open(file_path, 'r', encoding="utf-8") as f:
        words = f.readlines()
        word_set = set(m.strip() for m in words)
        return list(frozenset(word_set))


stopwords = open_text_file('stopwords.txt')
adjectives = open_text_file('adjective_list.txt')


def init_word_lists():
    print("Initializing words")

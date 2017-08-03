from __future__ import print_function
from sklearn.feature_extraction.text import TfidfVectorizer
from subprocess import Popen, PIPE
import numpy as np
import re
from nltk.corpus import stopwords, wordnet
from nltk.stem import SnowballStemmer
from gensim import models, similarities
from textblob import TextBlob
from django.conf import settings
import scipy as sp
from scipy import sparse
import joblib
import pickle
import os.path
import time
import os
from django.core.cache import cache
import fnmatch

ROOT = os.path.dirname(os.path.abspath(__file__))


def prepare_request(request):
    request = re.sub(r"(\n)", " ", request.lower())
    request = re.sub(r"(-\n)", "", request)
    request = re.split("[^a-z0-9]", request)
    stop_words = stopwords.words('english')
    stemmer = SnowballStemmer('english')

    request = [stemmer.stem(word) for word in request if (word not in stop_words) & (len(word) > 1) & (len(word) < 20)]
    return ' '.join(request)


def dist_raw(v1, v2):
    delta = v1 - v2
    return sp.linalg.norm(delta.toarray())


def cos_raw(v1, v2):
    return sp.spatial.distance.cosine(v1.toarray(), v2.toarray())


def range_search(vec_request, corpus):
    distances = []
    for i, doc in enumerate(corpus):
        vec = corpus.getrow(i)
        distances.append((cos_raw(vec, vec_request), i))
    return distances


# celery - bg tasks
model = None
index = None
corpora_dictionary = None


def lda_search(request, model_name):
    start = time.time()

    MODEL_PATH = os.path.join(ROOT, "models/" + model_name + ".model")
    INDEX_PATH = os.path.join(ROOT, "models/lda_MatrixSimilarity" + model_name + ".index")
    CORPORA_DICTIONARY_PATH = os.path.join(ROOT, "models/corpora_dictionary.pickle")

    '''model = cache.get('model')
    index = cache.get('index')
    corpora_dictionary = cache.get('corpora_dictionary')'''

    global model
    global index
    global corpora_dictionary

    if model == None:
        model = models.LdaModel.load(MODEL_PATH)
    if index == None:
        index = similarities.MatrixSimilarity.load(INDEX_PATH)
    if corpora_dictionary == None:
        with open(CORPORA_DICTIONARY_PATH, 'rb') as f:
            corpora_dictionary = pickle.load(f)

    print("Loaded model in %f seconds" % (time.time() - start))

    start2 = time.time()
    request = prepare_request(request)
    print("Prepared request in %f seconds" % (time.time() - start2))

    start1 = time.time()
    vec = corpora_dictionary.doc2bow(re.split(' ', request))
    topics = model[vec]

    key_words = set()
    [key_words.update([key[0] for key in model.show_topic(topic_index, topn=20)])
     for topic_index in [topic[0] for topic in topics]]

    related_themes = [(topic[0], topic[1]) for topic in topics]

    sims = index[topics]
    sims = sorted(enumerate(sims), key=lambda item: -item[1])
    print("Vectorizing and sims finding completed in %f seconds" % (time.time() - start1))

    print("Lda search completed in %f seconds" % (time.time() - start))
    return sims, related_themes


def print_highlighted_doc(doc, key_words):
    highlighted_doc = ""
    str_len = 0
    for word in re.split(' ', doc):
        if word in re.split(' ', key_words):
            highlighted_doc += "\033[44;38m" + word + "\033[m "
        else:
            highlighted_doc += word + " "
        str_len += len(word)
        if str_len > 100:
            str_len = 0
            highlighted_doc += "\n"
    print(highlighted_doc + "\n")


def print_n_docs(files, distances, key_words, num_sims=1):
    for i in range(num_sims):
        print("Distance: ", distances[i][0])
        print_highlighted_doc(files[distances[i][1]], key_words)


def get_ngrams(doc, n):
    blob = TextBlob(doc)
    ngrams = blob.ngrams(n=n)
    return ngrams


def add_synonyms(request):
    extended_request = set()
    for word in request:
        synonyms = wordnet.synsets(word)
        for syn in synonyms:
            extended_request.update(syn.lemma_names())
    return list(extended_request)


def vec_search(vectorizer, corpus, request):
    request = prepare_request(request)
    key_words = request
    request = vectorizer.transform([request])
    distances = range_search(request, corpus)
    distances = sorted(distances, key=lambda item: item[0])
    return distances, key_words


def create_vectorizer():
    PROCESSED_FILES_PATH = os.path.join(ROOT, "models/processed_files.pickle")
    CORPUS_PATH = os.path.join(ROOT, "models/vectorizer_corpus.npy")
    VECTORIZER_PATH = os.path.join(ROOT, 'models/vectorizer.pkl')

    with open(PROCESSED_FILES_PATH, 'rb') as f:
        processed_files = pickle.load(f)

    try:
        corpus = sparse.csr_matrix(np.load(CORPUS_PATH))
        vectorizer = joblib.load(VECTORIZER_PATH)
        print("vectorizer loaded")

    except:
        vectorizer = TfidfVectorizer(min_df=1)
        corpus = vectorizer.fit_transform(processed_files)
        joblib.dump(vectorizer, VECTORIZER_PATH)
        np.save(os.path.join(ROOT, "models/vectorizer_corpus"), np.array(corpus.toarray()))
        print("vectorizer created and saved")

    return vectorizer, corpus, processed_files


def find_files(source_path, mask):
    found_files = []
    for root, dirs, files in os.walk(source_path):
        found_files += [os.path.join(root, name) for name in files if fnmatch.fnmatch(name, mask)]
    return found_files


'''(request, num_docs) -> [(doc_id, weight)]'''
def get_articles(request, num_docs):
    start = time.time()
    MODEL_NAME = "lda3"
    SOURCE_TXTS_PATH = os.path.join(ROOT, 'source_txts/')

    source_files = find_files(SOURCE_TXTS_PATH, "*.txt")
    similar, related_themes = lda_search(request, MODEL_NAME)
    answer = []
    for sim in similar[:num_docs]:
        doc_id = "id" + source_files[sim[0]][-14:-4]
        answer.append((doc_id, sim[1]))
    print("All search completed in %f seconds" % (time.time() - start))
    return answer, related_themes


def convert(out_path, input_path):
    print("convert")
    cmd2 = "pdf2txt.py "
    cmd = cmd2 + " -o " + out_path + " " + input_path
    # print(cmd)
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)


def process_txt_file(file_name):
    return open(os.path.join(settings.MEDIA_ROOT, file_name), 'r').read()


def process_pdf_file(file_name):
    # text = open(os.path.join(settings.MEDIA_ROOT, 'a.txt'), 'rb').read()
    print(os.path.join(settings.MEDIA_ROOT, file_name))
    # print("process pdf file")
    # convert("./tmp.txt", file.name)



    # print(get_articles("neural networks"))


    # create_vectorizer()
    # doc_search(os.path.join(ROOT, "models/processed_files.npy"))

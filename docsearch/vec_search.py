from __future__ import print_function
from sklearn.feature_extraction.text import TfidfVectorizer
from subprocess import Popen, PIPE
import numpy as np
import re
from nltk.corpus import stopwords, wordnet
from nltk.stem import SnowballStemmer
from gensim import corpora, models, similarities
from textblob import TextBlob
from django.conf import settings
import requests
import scipy as sp
from scipy import sparse
import joblib
import pickle
import os.path
import time
import os
import fnmatch

ROOT = os.path.dirname(os.path.abspath(__file__))

def prepare_request(request, synonyms = False):
    request = re.sub(r"(\n)", " ", request.lower())
    request = re.sub(r"(-\n)", "", request)
    request = re.split("[^a-z0-9]", request)
    stop_words = stopwords.words('english')
    stemmer = SnowballStemmer('english')
    if synonyms == True:
        request = add_synonyms([word for word in request if word not in stop_words])
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

#celery - bg tasks
def lda_search(request, model_name):
    prepare_request(request)

    MODEL_PATH = os.path.join(ROOT, "models/" + model_name + ".model")
    INDEX_PATH = os.path.join(ROOT, "models/lda_MatrixSimilarity" + model_name + ".index")
    CORPORA_DICTIONARY_PATH = os.path.join(ROOT, "models/corpora_dictionary.pickle")

    with open(CORPORA_DICTIONARY_PATH, 'rb') as f:
        corpora_dictionary = pickle.load(f)

    model = models.LdaModel.load(MODEL_PATH)
    index = similarities.MatrixSimilarity.load(INDEX_PATH)

    vec = corpora_dictionary.doc2bow(re.split(' ', request))
    topics = model[vec]
    '''key_words = set()
    [key_words.update([key[0] for key in model.show_topic(topic_index, topn=20)])
     for topic_index in [topic[0] for topic in topics]]
     '''

    sims = index[topics]
    sims = sorted(enumerate(sims), key=lambda item: -item[1])
    return sims


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

def print_n_docs(files, distances, key_words, num_sims = 1):
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
    find_files = []
    for root, dirs, files in os.walk(source_path):
        find_files += [os.path.join(root, name) for name in files if fnmatch.fnmatch(name, mask)]
    return find_files

def make_id_name(i):
    zeros = ""
    for j in range(5 - len(str(i))):
        zeros += "0"
    id_name = zeros + str(i)
    return id_name

'''(request) -> [(name, abstract, url)]'''
def get_articles(request):
    MODEL_NAME = "lda3"
    NUM_DOCS = 100
    META_INFO_PATH = os.path.join(ROOT, 'meta_archive_info/')
    SOURCE_TXTS_PATH = os.path.join(ROOT, 'source_txts')

    source_files = find_files(SOURCE_TXTS_PATH, "*.txt")

    with open(os.path.join(META_INFO_PATH, 'meta.pickle'), 'rb') as f:
        meta = pickle.load(f)


    start = time.time()
    '''lda_search(request, MODEL_NAME) -> [(index, weight)]'''
    similar = lda_search(request, MODEL_NAME)
    answer = []
    for sim in similar[:NUM_DOCS]:
        doc_id = "id" + source_files[sim[0]][-14:-4]
        print(doc_id)
        if len(meta[doc_id]) > 0:
            article = meta[doc_id]
            answer.append((article['title'],
                           article['description'],
                           "http://arxiv.org/abs/" + doc_id[2:]))
    print("Found in %f time" %(time.time() - start))
    return answer


def convert(out_path, input_path):
    print("convert")
    cmd2 = "pdf2txt.py "
    cmd = cmd2 + " -o " + out_path + " " + input_path
    #print(cmd)
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)

def process_txt_file(file_name):
    return open(os.path.join(settings.MEDIA_ROOT, file_name), 'r').read()

def process_pdf_file(file_name):
    #text = open(os.path.join(settings.MEDIA_ROOT, 'a.txt'), 'rb').read()
    print(os.path.join(settings.MEDIA_ROOT, file_name))
    #print("process pdf file")
    #convert("./tmp.txt", file.name)



#print(get_articles("neural networks"))


#create_vectorizer()
#doc_search(os.path.join(ROOT, "models/processed_files.npy"))
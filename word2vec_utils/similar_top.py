# coding=utf-8
import argparse, codecs
from sys import stderr, stdin, stdout
from .utils import load_vectors
import re
from time import time
import numpy as np
from collections import OrderedDict, defaultdict
import sys, traceback
from .parallel import parallel_map

from math import ceil
from sys import stderr
__author__ = 'nvanva'

re_only_letters = re.compile(r'[^\W\d_]', re.U)

def load_freq(freq_file):
    print("Loading frequencies")
    d = defaultdict(int)
    with codecs.open(freq_file, 'r', encoding='utf-8') as f:
        for line in f:
            (key, val) = line.split()
            d[key] = int(val)
    return d

def similar_top(vec, words, topn=250):
    res = OrderedDict()
    for word in words:
        res[word] = vec.most_similar(positive=[word],negative=[], topn=topn)
    return res

def argmax_k(dists, topn):
    dists = -dists
    return np.argpartition(dists, topn,axis=1)[:,:topn]

def similar_top_opt(vec, words, topn=250):
    vec.init_sims()

    indices = [vec.vocab[w].index for w in words if w in vec.vocab]
    vecs = vec.syn0norm[indices]
    dists = np.dot(vecs, vec.syn0norm.T)
    best = argmax_k(dists,topn)

    res = OrderedDict()
    for i in range(len(indices)):
        sims = best[i,np.argsort(-dists[i, best[i]])] 
        ns = [(vec.index2word[sim], float(dists[i, sim])) for sim in sims if sim!=indices[i]]
        res[vec.index2word[indices[i]]] = ns
    return res


def dists2neighbours(vec, dists, indices, topn):
    # dist shape is (current_batch x vocabulary_size)
    best = argmax_k(dists,topn)

    res = OrderedDict()
    for i in range(len(indices)):
        sims = best[i,np.argsort(-dists[i, best[i]])] # sims is a list of indices (in relation to syn0norm) of nearest neighbours
                                                      # sorted(!) by similarity
        ns = [(vec.index2word[sim], float(dists[i, sim])) for sim in sims if sim!=indices[i]]
        res[vec.index2word[indices[i]]] = ns
    return res

def order_freq(vec, freq):
    "return frequencies of words as an array ordered excatly as words in vec.syn0norm"
    l = []
    for i in range(len(vec.syn0norm)):
        if freq[vec.index2word[i]] > 0:
            l.append(freq[vec.index2word[i]])
        else: 
            l.append(1) # neutral frequency for words with unknown frequency

    return np.array(l)
    
def similar_top_opt3(vec, words, topn=200, nthreads=4, freq=None):
    vec.init_sims()

    indices = [vec.vocab[w].index for w in words if w in vec.vocab]
    vecs = vec.syn0norm[indices]
    dists = np.dot(vecs, vec.syn0norm.T)
    
    if freq is not None:
        dists = dists * np.log(freq)

    if nthreads==1:
        res = dists2neighbours(vec, dists, indices, topn)
    else:
        batchsize = int(ceil(1. * len(indices) / nthreads))
        print("dists2neighbours for %d words in %d threads, batchsize=%d" % (len(indices), nthreads, batchsize), file=stderr)
        def ppp(i):
            return dists2neighbours(vec, dists[i:i+batchsize], indices[i:i+batchsize], topn)
        lres = parallel_map(ppp, list(range(0,len(indices),batchsize)), threads=nthreads)
        res = OrderedDict()
        for lr in lres:
            res.update(lr)

    return res


def print_similar(out, vectors, batch, mindist=None, only_letters=False, pairs=False, freq=None):
    try:
        for word, ns in similar_top_opt3(vectors, batch, freq=freq).items():
            sims = []
            for w, d in ns:
                if (mindist is None or d >= mindist) and (not only_letters or re_only_letters.match(w) is not None):
                    # print >> stderr, "%s: RETURNED\t%s\t%r" % (word.encode('utf8'), w.encode('utf8'), sim)
                    sims.append((w, d))
                else:
                    print("%s: SKIPPED\t%s\t%r" % (word.encode('utf8'), w.encode('utf8'), d), file=stderr)

            if pairs:
                print('\n'.join(("%s\t%s\t%f" % (word.encode('utf8'), w.encode('utf8'), d) for w, d in sims)), file=out)
            else:
                print("%s\t%s" % (word.encode('utf8'), ','.join(("%s:%f" % (w.encode('utf8'), d) for w, d in sims))), file=out)

            #print >> stderr, "%s: %d similar words found" % (word.encode('utf8'), len(sims))
    except:
        print("ERROR in print_similar()", file=stderr)
        traceback.print_exc(file=sys.stderr)


def process(out, vectors, words, only_letters, batch_size=1000, pairs=False, freq=None):
    batch = []
    for word in words:#vectors.index2word[:vocab_size]:
        try:
            word = word.rstrip('\n')
        except UnicodeDecodeError:
            print("couldn't decode word from stdout, skipped", file=stderr)
            continue
        if only_letters and re_only_letters.match(word) is None:
            print("%s: SKIPPED_ALL" % word, file=stderr)
            continue

        batch.append(word)

        if len(batch) >=  batch_size:
            print_similar(out, vectors, batch, only_letters=only_letters, pairs=pairs, freq=freq)
            batch = []

    if len(batch) > 0:
        print_similar(out, vectors, batch, only_letters=only_letters, pairs=pairs, freq=freq)

def init(fvec, output="", only_letters=False, vocab_limit=None, pairs=False, batch_size=1000, word_freqs=None):

    print("Vectors: {}, only_letters: {}".format(fvec, only_letters), file=stderr)
    print("Loading vectors from {}".format(fvec), file=stderr)
    tic = time()
    vectors = load_vectors(fvec, binary=True)
    print("Vectors loaded in %d sec." % (time()-tic), file=stderr)
    print("Vectors shape is: ", vectors.syn0norm.shape, file=stderr)

    vocab_size = len(vectors.vocab)
    print(("Vocabulary size: %i" % vocab_size))
    
    # Limit the number of words for which to collect neighbours
    if vocab_limit and vocab_limit < vocab_size:
        vocab_size = vocab_limit
    words = vectors.index2word[:vocab_size]
    
    print(("Collect neighbours for %i most frequent words" % vocab_size))
    
    freq=None
    if word_freqs:
        freq_dict = load_freq(word_freqs)
        freq = order_freq(vectors, freq_dict)
        print("freqs loaded. Length ", len(freq), freq[:10])

    with codecs.open(output, 'wb') if output else stdout as out:
        process(out, vectors, words, only_letters=only_letters, batch_size=batch_size, pairs=pairs, freq=freq)

def main():
    parser = argparse.ArgumentParser(
        description='Efficient computation of nearest word neighbours.')
        #description='Reads words from vector model. Writes to output word + similar words and their distances to the original word.')
    parser.add_argument('vectors', help='Word2vec word vectors file.', default='')
    parser.add_argument('-output', help='Output file in on-pair-per-line format, gziped', default='')
    parser.add_argument('-only_letters', help='Skip words containing non-letter symbols from stding / similar words.', action="store_true")
    parser.add_argument("-vocab_limit", help="Collect neighbours only for specified number of most frequent words. By default use all words.", default=None, type=int)
    parser.add_argument('-pairs', help="Use pairs format: 2 words and distance in each line. Otherwise echo line is a word and all it's neighbours with distances." , action="store_true")
    parser.add_argument('-batch-size', help='Batch size for finding neighbours.', default="1000")
    parser.add_argument('-word_freqs', help="Weight similar words by frequency. Pass frequency file as parameter", default=None)

    args = parser.parse_args()
     
    init(args.vectors, output=args.output, only_letters=args.only_letters, vocab_limit=args.vocab_limit, pairs=args.pairs, batch_size=int(args.batch_size), word_freqs=args.word_freqs)

if __name__ == '__main__':
    main()

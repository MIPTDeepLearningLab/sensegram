## fork_update {

Project was successfully transfered to py3 and tested with `python 3.6.3`.

**Unfortunately this version of the project is deprecated, thus it is worthwhile to check the original repository for the maintenance of the third python.**


#### Installation:

1. You should install [`maven`](https://maven.apache.org/install.html) because it is required for `chinese-whispers` implemented in java.

2. All the following installation process is the same as in original package.

```
git clone https://github.com/fogside/sensegram.git

cd sensegram/

pip install -r requirements.txt

./init.sh
```

### }

---

# SenseGram

This repository contains implementation of a method that takes as an input a word embeddings, such as word2vec and splits different senses of the input words. For instance, the vector for the word "table" will be split into "table (data)" and "table (furniture)" as shown below.

Our method performs word sense induction and disambiguation based on sense embeddings. Sense inventory is induced from exhisting word embeddings via clustering of ego-networks of related words.

Detailed description of the method is available in the original paper:

- [**Original paper**](http://aclweb.org/anthology/W/W16/W16-1620.pdf)
- [**Presentation**](docs/presentation.pdf)
- [**Poster**](docs/poster.pdf)

![ego](docs/table3.png)


If you use the method please cite the following paper:

```
@InProceedings{pelevina-EtAl:2016:RepL4NLP,
  author    = {Pelevina, Maria  and  Arefiev, Nikolay  and  Biemann, Chris  and  Panchenko, Alexander},
  title     = {Making Sense of Word Embeddings},
  booktitle = {Proceedings of the 1st Workshop on Representation Learning for NLP},
  month     = {August},
  year      = {2016},
  address   = {Berlin, Germany},
  publisher = {Association for Computational Linguistics},
  pages     = {174--183},
  url       = {http://anthology.aclweb.org/W16-1620}
}
```

## Installation
This project is implemented in Python 2.7. 
It makes use of a modified implementation of word2vec toolkit that saves context vectors ([word2vec_c](word2vec_c/)) and a clustering algorithm [chinese-whispers](chinese-whispers/), both distributed with this package. 

It has been tested on Linux. It should work on Mac too, but you may encounter problems with compilation of word2vec. If you do, read [this](word2vec_c/mac_install.txt).

To install SenseGram run the following commands:

```
git clone https://github.com/tudarmstadt-lt/sensegram.git
cd sensegram/
./init.sh
```

The `init.sh` script will create necessary subdirectories, compile word2vec and chinese-whispers (compilation of chinese-whispers requires maven).

To install required Python packages run:

```
pip install -r requirements.txt
```
or use your own package manager.

## Training a model
The best way to train your own sense model is with the `train.py` script. You will have to provide a tokenized corpus as input. For tokenization you can use the [preprocessing](corpora/preprocess.py) script (it uses Treebank tokenizer and keeps letter cases, numbers and punctuation intact).

If you run `train.py` with no parameters, it will print usage information:

```
[-h] [-cbow CBOW] [-size SIZE] [-window WINDOW]
                [-threads THREADS] [-iter ITER] [-min_count MIN_COUNT]
                [-only_letters] [-vocab_limit VOCAB_LIMIT] [-N N] [-n N]
                [-min_size MIN_SIZE] [-pooling_method POOLING_METHOD]
                train_corpus
```

Here is the description of all parameters:

For Stage 1 (training of word/context vectors with word2vec)

* `train_corpus` is a path to a training corpus
* `-cbow` set 1 to use the CBOW model; set 0 for Skip-gram model
* `-size` is the dimensionality of learned vectors
* `-window` is the max context window length
* `-threads` is the number of threads
* `-iter` is the number of training iterations
* `-min_count` specifies the minimum word count below which word will be ignored.

For Stage 2 (calculating word similarity graph)

* `-only_letters` if set, words containg characters different from letters/dash/point will be ignored
* `-vocab_limit` is the number of most frequent words for which to collect nearest neighbours

For Stage 3 (clustering of ego-networks)

* `-N` is the number of nodes in each ego-network. We suggest to use 200.
* `-n` is the max number of edges for each node in the network. Regulatedcluster granularity (smaller n, more clusters).
* `-min_size` is the minimum size of the sense cluster. Consider values between 5-15, depending on N.

For Stage 4 (pooling of word vectors)

* `-pooling_method` specifies which pooling method to use: 'mean' or 'weighted_mean'. Weighted mean is consistently better.


The training produces following output files:

* `model/ + CORPUS_NAME + .words` - word vectors
* `model/ + CORPUS_NAME + .contexts` - context vectors
* `model/ + CORPUS_NAME + .senses.w2v` - sense vectors
* `model/ + CORPUS_NAME + .senses.w2v.probs` - sense probabilities  

In addition, it produces several intermediary files that can be investigated for error analysis or removed after training:

* `intermediate/ + CORPUS_NAME + .neighbours` - word similarity graph (distributional thesaurus) 
* `intermediate/ + corpus_name + .clusters` - sense clusters produced by chinese-whispers
* `intermediate/ + corpus_name + .minsize + MIN_SIZE` - clusters that remained after filtering out of small clusters 
* `intermediate/ + corpus_name + .filtered` - clusters that were filtered out    
* `intermediate/ + corpus_name + .inventory` - sense inventory that exactly corresponds to produced sense vectors

In [demo_train.sh](demo_train.sh) we provide an example for usage of the `train.py` script.

Note: This project implements the induction of word senses via clustering of ego-networks built with word2vec word similarities. To use JoBimText similarities you need a sense inventory produced by JoBimText, which you can pass as input to Stage 4 of the training pipeline.

## Playing with the model
To play with word sense embeddings you can use a pretrained model (sense vectors and sense probabilities). These sense vectors were induced from English Wikipedia using word2vec similarities between words in ego-networks. Probabilities are stored in a separate file and are not strictly necessary (if absent, the model will assign equal probabilities for every sense). To download the model call:

```
wget http://panchenko.me/data/joint/sensegram/wiki.senses.w2v 	// sense vectors
wget http://panchenko.me/data/joint/sensegram/wiki.senses.w2v.probs	// sense probabilities
```

To load sense vectors:

```
$ python
>>> import sensegram
>>> sv = sensegram.SenseGram.load_word2vec_format(path_to_model/wiki.senses.w2v, binary=True)
```
Probabilities of senses will be loaded automatically if placed in the same folder as sense vectors and named according to the same scheme as our pretrained files.

To examine how many senses were learned for a word call `get_senses` funcion:

```
>>> sv.get_senses("table")
[('table#0', 0.40206185567), ('table#1', 0.59793814433)]
```
The function returns a list of sense names with probabilities for each sense. As one can see, our model has learned two senses for the word "table".

To understand which word sense is represented with a sense vector use `most_similar` function:

```
>>> sv.most_similar("table#1")
[('pile#1', 0.9263191819190979),
 ('stool#1', 0.918972909450531),
 ('tray#0', 0.9099194407463074),
 ('basket#0', 0.9083326458930969),
 ('bowl#1', 0.905775249004364),
 ('bucket#0', 0.895959198474884),
 ('box#0', 0.8930465579032898),
 ('cage#0', 0.8916786909103394),
 ('saucer#3', 0.8904291391372681),
 ('mirror#1', 0.8880348205566406)]
```
For example, "table#1" represents the sense related to furniture.

To use our word sense disambiguation mechanism you also need word vectors or context vectors, depending on the dismabiguation strategy. Those word and context vectors should be trained on the same corpus as sense vectors. You can download word and context vectors pretrained on English Wikipedia here:

```
wget http://panchenko.me/data/joint/sensegram/wiki.words	// word vectors
wget http://panchenko.me/data/joint/sensegram/wiki.contexts	// context vectors
```

Our WSD mechanism supports two disambiguation strategies: one based on word similarities (`sim`) and another based on word probabilities (`prob`). The first one requires word vectors to represent context words and the second one requires context vectors for the same purpose. In following we provide a disambiguation example using similarity strategy.

First, load word vectors using gensim library:

```
from gensim.models import word2vec
wv = word2vec.Word2Vec.load_word2vec_format(path_to_model/wiki.words, binary=True)
```

Then initialise the WSD object with sense and word vectors:

```
wsd_model = sensegram.WSD(sv, wv, window=5, method='sim', filter_ctx=3)
```
The settings have the following meaning: it will extract at most `window`*2 words around the target word from the sentence as context and it will use only three most discriminative context words for disambiguation. 

Now you can disambiguate the word "table" in the sentence "They bought a table and chairs for kitchen" using `dis_text` function. As input it takes a sentence with space separated tokens, a target word, and start/end indices of the target word in the given sentence.

```
>>> wsd_model.dis_text("They bought a table and chairs for kitchen", "table", 14, 19)
(u'table#1', [0.15628162913257754, 0.54676466664654355])
```
It outputs its guess of the correct sense, as well as scores it assigned to all known senses during disambiguation. As one can see, it guessed the correct sense of the word "table" related to the furniture. The vector for this sense can be obtained from `sv["table#1"]`.

## Pretrained models
We provide several pretrained sense models accompanied by word and context vectors necessary for disambiguation. We have trained them on two corpora: English Wikipedia dump and UKWaC.

#### English Wikipedia

Word and context vectors:

```
wget http://panchenko.me/data/joint/sensegram/wiki.words
wget http://panchenko.me/data/joint/sensegram/wiki.contexts
```
Those vectors are of size 300, trained with CBOW model using 3-words context window, 3 iterations and minimum word frequency of 5.

Senses and probabilities induced using word2vec similarities between words:

```
wget http://panchenko.me/data/joint/sensegram/wiki.senses.w2v
wget http://panchenko.me/data/joint/sensegram/wiki.senses.w2v.probs
```

Senses and probabilities induced using JoBimText similarities between words:

```
wget http://panchenko.me/data/joint/sensegram/wiki.senses.jbt
wget http://panchenko.me/data/joint/sensegram/wiki.senses.jbt.probs
```

#### UKWaC

Word and context vectors:

```
wget http://panchenko.me/data/joint/sensegram/ukwac.words
wget http://panchenko.me/data/joint/sensegram/ukwac.contexts
```
Those vectors are of size 100, trained with CBOW model using 3-words context window, 3 iterations and minimum word frequency of 5.

Senses and probabilities induced using word2vec similarities between words:

```
wget http://panchenko.me/data/joint/sensegram/ukwac.senses.w2v
wget http://panchenko.me/data/joint/sensegram/ukwac.senses.w2v.probs
```

Senses and probabilities induced using JoBimText similarities between words:

```
wget http://panchenko.me/data/joint/sensegram/ukwac.senses.jbt
wget http://panchenko.me/data/joint/sensegram/ukwac.senses.jbt.probs
```

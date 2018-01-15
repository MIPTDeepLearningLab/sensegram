#! /usr/bin/env python
# -*- coding: utf-8 -*-
import argparse, codecs
from pandas import read_csv
from csv import QUOTE_NONE
from sensegram import WSDdep, SenseGram
from gensim.models import word2vec
import pbar

n_neighbours = 50

def run(test_file, sense, context, sense_dep, context_dep, output, wsd_method='sim', filter_ctx=2, lowercase=False, ignore_case=False):
    
    print("Loading models...")
    vs = SenseGram.load_word2vec_format(sense, binary=True)
    vc = word2vec.Word2Vec.load_word2vec_format(context, binary=True)
    vs_dep = SenseGram.load_word2vec_format(sense_dep, binary=True)
    vc_dep = word2vec.Word2Vec.load_word2vec_format(context_dep, binary=False)
   
    wsd_model = WSDdep(vs, vc, vs_dep, vc_dep, method=wsd_method, filter_ctx=filter_ctx, ignore_case=ignore_case)

    print("Loading test set...")
    reader = read_csv(test_file, encoding="utf-8", delimiter="\t", dtype={'predict_related': object, 'gold_sense_ids':object, 'predict_sense_ids':object, 'deps':object})
    rows_count = reader.shape[0]
    print((str(rows_count) + " test instances"))
    pb = pbar.Pbar(rows_count, 100)
    

    uncovered_words = [] # target words for which sense model has zero senses

    print(("Start prediction over " + test_file))
    pb.start()
    reader = reader.fillna('')
    for i, row in reader.iterrows():
        ctx = row.context.lower() if lowercase else row.context
        start, end = [int(x) for x in row.target_position.split(',')]
        
        if row.deps == "ParseError" or row.deps == "":
            deps = []
        else: 
            deps = [dep for dep in row.deps.split() if dep in vc.vocab]
            
        prediction = wsd_model.dis(ctx, row.target, start, end, deps)
        
        if prediction:
            sense, sense_scores = prediction
            reader.set_value(i, 'predict_sense_ids', sense.split("#")[1])
                #neighbours = wsd_model.vs.most_similar(sense, topn=n_neighbours)
                #neighbours = ["%s:%.3f" % (n.split("#")[0], float(sim)) for n, sim in neighbours]
                #reader.set_value(i, 'predict_related', ",".join(neighbours))
        else:
            uncovered_words.append(row.target)
            continue
            
        pb.update(i)
    pb.finish()
    
    reader.to_csv(sep='\t', path_or_buf=output, encoding="utf-8", index=False, quoting=QUOTE_NONE)
    print(("Saved predictions to " + output))
    

def main():
    parser = argparse.ArgumentParser(description='Fill in a test dataset for word sense disambiguation.')
    parser.add_argument('test_file', help='A path to a test dataset. Format: "context_id<TAB>target<TAB>target_pos<TAB>target_position<TAB>gold_sense_ids<TAB>predict_sense_ids<TAB>golden_related<TAB>predict_related<TAB>context')
    parser.add_argument("sense", help="A path to a sense vector model")
    parser.add_argument("context", help="A path to a context vector model")
    parser.add_argument("sense_dep", help="A path to a sense dep-based vector model")
    parser.add_argument("context_dep", help="A path to a context dep-based vector model")
    parser.add_argument("output", help="An output path to the filled dataset. Same format as test_file")
    parser.add_argument("-wsd_method", help="WSD method 'prob' or 'sim'. Default='sim'", default="sim")
    parser.add_argument("-filter_ctx", help="Number of context words for WSD (-1 for no filtering). Default is 2.", default=2, type=int)
    parser.add_argument("-lowercase_context", help="Lowercase all words in context (necessary if context vector model only has lowercased words). Default False", action="store_true")
    parser.add_argument("-ignore_case", help="Ignore case of a target word (consider upper- and lower-cased senses). Default False", action="store_true")
    args = parser.parse_args()

    run(args.test_file, args.sense, args.context, args.sense_dep, args.context_dep, args.output, args.wsd_method, args.filter_ctx, args.lowercase_context, args.ignore_case) 
    
if __name__ == '__main__':
    main()

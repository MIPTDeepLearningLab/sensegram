#!/usr/bin/env bash

if [ ! -e text8 ]; then
  wget http://mattmahoney.net/dc/text8.zip -O text8.zip
  unzip text8.zip
fi

python train.py text8 -cbow 1 -size 100 -window 3 -threads 4 -iter 3 -min_count 5 -only_letters -n 200 -N 200 -min_size 5

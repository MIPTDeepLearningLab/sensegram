install:
	pip install -r requirements.txt	
	git submodule init
	git submodule update
	cd word2vec/src; make
	cd chinese-whispers; mvn package shade:shade 
	mkdir model
	mkdir intermediate

download:
	wget http://panchenko.me/data/joint/sensegram/wiki.senses.w2v
	wget http://panchenko.me/data/joint/sensegram/wiki.senses.w2v.probs
	wget http://panchenko.me/data/joint/sensegram/wiki.words
	wget http://panchenko.me/data/joint/sensegram/wiki.contexts
	wget http://panchenko.me/data/joint/sensegram/wiki.senses.jbt
	wget http://panchenko.me/data/joint/sensegram/wiki.senses.jbt.probs
	wget http://panchenko.me/data/joint/sensegram/wiki.senses.twsi
	wget http://panchenko.me/data/joint/sensegram/wiki.senses.twsi.probs
	wget http://panchenko.me/data/joint/sensegram/ukwac.words
	wget http://panchenko.me/data/joint/sensegram/ukwac.contexts
	wget http://panchenko.me/data/joint/sensegram/ukwac.senses.w2v
	wget http://panchenko.me/data/joint/sensegram/ukwac.senses.w2v.probs
	wget http://panchenko.me/data/joint/sensegram/ukwac.senses.jbt
	wget http://panchenko.me/data/joint/sensegram/ukwac.senses.jbt.probs
	wget http://panchenko.me/data/joint/sensegram/ukwac.senses.twsi
	wget http://panchenko.me/data/joint/sensegram/ukwac.senses.twsi.probs

train:
	bash demo_train.sh



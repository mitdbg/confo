#!/bin/bash


python2.7 parser.py ../data/dblp.xml 2>err
python2.7 loadparsed.py 2>>err

# calculate word frequencies
python2.7 stems.py
python2.7 words.py
python2.7 loadwords.py

# calculate other statistics
psql -f ./setup.sql confo confo
python2.7 precompute.py

python2.7 similar_conferences.py

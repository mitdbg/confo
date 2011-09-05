#!/bin/bash


python parser.py ../data/dblp.xml 2>err
python loadparsed.py 

# calculate word frequencies
python stems.py
python words.py
python loadwords.py

# calculate other statistics
python precompute.py

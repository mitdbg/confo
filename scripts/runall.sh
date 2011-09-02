#!/bin/bash

dropdb confo
createdb confo
python ../manage.py syncdb
python parser.py ../data/dblp.xml 2> err
python words.py
python loadwords.py
python ../manage.py runserver
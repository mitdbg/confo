#!/bin/bash
dropdb confo
createdb confo
rm err
python manage.py syncdb
python scripts/parser.py data/dblp.xml 2> err
python scripts/words.py
python scripts/loadwords.py
#python manage.py runserver

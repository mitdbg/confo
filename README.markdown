DBLP visualization 
===================

By eugene wu, adam marcus, sam madden


Setup
----------

Make sure the confo directory is in your PYTHONPATH, e.g.:
       export PYTHONPATH=/PATH/TO/CONFO/confo:$PYTHONPATH

Make sure django, nltk, and psycopg2 toolkits are installed:
       https://www.djangoproject.com/download/
       http://www.nltk.org/download
       http://initd.org/psycopg/download/


Create the django private_settings.py file:
       (from the top level confo directory)
       cp private_settings.py.tmpl private_settings.py
       (edit the file to add postgresql_psycopg2 to the ENGINE list, and add "confo" to the NAME list)

Download the data

        cd ./data
        ./getdblp.sh

Setup the database

      dropdb confo
      createdb confo
      createuser confo
      python manage.py syncdb
      python manage.py createcachetable cache

Parse and Load the database, and precompute some statistics

      cd ./scripts
      ./runall.sh
      
Run the server

    python manage.py runserver 0.0.0.0:8888
    http://localhost:8888     




Future Features List (TODOs)
----------------------

* Simple filtering -- e.g., see a subset of years, or a subset of conferences for a given author.
* Click on a keyword and see all the papers with that word in it for the given year/word
* "What's hot with XXX" -- sounds kinda weird
* In the little histograms, display maximum value is -- or show height on mouse over
* "Hide" a word.  Popular words (e.g., "data", "query") make it hard to see the other terms in the little plots.
* Compare two conferences or people (I'm not sure how that interface would even work)
* Slow query log like https://github.com/colinhowe/djangosqlsampler

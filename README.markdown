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
* Cluster authors by similarity
* Simple filtering -- e.g., see a subset of years, or a subset of conferences for a given author.
* Click on a keyword and see all the papers with that word in it for the given year/word
* "What's hot with XXX" -- sounds kinda weird
* In the little histograms, display maximum value is -- or show height on mouse over
* "Hide" a word.  Popular words (e.g., "data", "query") make it hard to see the other terms in the little plots.
* Compare two conferences or people (I'm not sure how that interface would even work)
* Slow query log like https://github.com/colinhowe/djangosqlsampler
* Show per-year words more compactly, or more vertically to avoid
in-page scrolling.  Maybe just show the top 5 TF-IDF terms for each
year in a more vertical layout, with a link to show all of the terms?
* It'd be awesome if the author term popularity graph were stacked and
filled.
* Might be cool to have links to papers that use a term under each term
(you'd have to go back to "hide" button for each term), though that's
probably unnecessary.
*  We should give links for conference years/paper titles to the
DBLP page for that item, if we can.
* We should give credit to DBLP for the data in the footer.
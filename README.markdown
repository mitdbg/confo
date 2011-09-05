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

Parse and Load the database, and precompute some statistics

      cd ./scripts
      ./runall.sh
      
Run the server

    python manage.py runserver 0.0.0.0:8888
    http://localhost:8888     
        
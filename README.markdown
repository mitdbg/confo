DBLP visualization 
===================

By eugene wu, adam marcus, sam madden


Setup
----------
        
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
        
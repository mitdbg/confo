import os
import sys
import nltk
import sqlite3
from nltk.corpus import stopwords

ROOT = os.path.abspath('%s/../..' % os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = 'confo.settings'
from django.core.management import setup_environ
from confo import settings
setup_environ(settings)
from confo.home.models import *
from django.db import connection, transaction


@transaction.commit_manually
def manage_indices(load_f):
    def retf():
        cur = connection.cursor()
        cur.execute("select * from pg_indexes where schemaname = 'public' and tablename='words';")
        createstmts = []
        ndropped = 0
        for _,tablename,indexname,_,createsql in cur:
            createstmts.append((tablename, indexname, createsql))


        for tablename, indexname,_ in createstmts:
            q1 = "drop index %s cascade;" % indexname
            q2 = "alter table %s drop contraint %s cascade;" % (tablename, indexname)
            
            try:
                print q1
                cur.execute(q1)
                ndropped += 1
                transaction.commit()
            except Exception, e:
                print e
                transaction.rollback()
                try:
                    print q2                
                    cur.execute(q2)
                    ndropped += 1
                    transaction.commit()
                except Exception, ee:
                    print ee
                    transaction.rollback()

        print "dropped %d indices." % ndropped                    
        if ndropped != len(createstmts):
            print "didn't drop all indexes.  exiting"
            return


        
        try:
            load_f()
            transaction.commit()
        except:
            transaction.rollback()

        for _,_,createstmt in createstmts:
            cur.execute(createstmt)

        cur.execute("select indexname from pg_indexes where schemaname = 'public';")
        print "created %d indices." % len(cur.fetchall())        
            
        transaction.commit()
    return retf


@transaction.commit_manually
@manage_indices
def load_db():
    query = "COPY %s (%s) FROM STDIN WITH CSV;" % ('words', ", ".join(['pid', 'word']))
    cmd = "cat ./allwords.txt | psql -c \"%s\" confo confo" % (query)
    os.system(cmd)

if __name__ == '__main__':
    load_db()

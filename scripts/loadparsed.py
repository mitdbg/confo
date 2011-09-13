import os
import sys

ROOT = os.path.abspath('%s/../..' % os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = 'confo.settings'
from django.core.management import setup_environ
from confo import settings
setup_environ(settings)
from confo.home.models import *
from django.db import connection, transaction
from dblogging import load_logger



@transaction.commit_manually
def manage_indices(load_f):
    def retf():
        cur = connection.cursor()
        cur.execute("select tablename, indexname, indexdef from pg_indexes where schemaname = 'public';")
        createstmts = []
        ndropped = 0

        for tablename,indexname,createsql in cur:
            createstmts.append((tablename, indexname, createsql))


        for tablename, indexname,_ in createstmts:
            try:
                sql = "drop index if exists %s" % indexname
                cur.execute(sql)
                ndropped += 1
                transaction.commit()
            except Exception, e:
                print >> sys.stderr, "error running: %s" % sql
                print >> sys.stderr, e
                transaction.rollback()

                try:
                    sql = "alter table %s drop constraint if exists %s cascade" % (tablename, indexname)
                    print "running", sql
                    cur.execute(sql)
                    ndropped += 1
                    transaction.commit()
                except Exception, e:
                    print >> sys.stderr, "error running: %s" % sql                
                    print >> sys.stderr, e
                    transaction.rollback()

        print "dropped %d indices." % ndropped
        

        load_f()

        ncreated = 0
        for _,_,createstmt in createstmts:
            try:
                print "running:", createstmt
                cur.execute(createstmt)
                ncreated += 1
                transaction.commit()
            except Exception, e:
                print >> sys.stderr, "error running: %s" % createstmt
                print >> sys.stderr, e
                transaction.rollback()
        print "created %d indices." % ncreated
            
        transaction.commit()
    return retf



@transaction.commit_manually
@manage_indices
def load_db():
    try:
        (confcache, confycache, authcache, papercache, pacache) = load_logger("r")
        cursor = connection.cursor()
        confcache.logtodb(cursor)
        confycache.logtodb(cursor)
        papercache.logtodb(cursor)
        authcache.logtodb(cursor)
        pacache.logtodb(cursor)
        transaction.commit()
    except Exception, e:
        transaction.rollback()
        raise

if __name__ == '__main__':
    load_db()

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




def l2norm(vec):
    sum_squares = sum(count*count for wid, count in vec)
    return sum_squares ** 0.5

def similarity(vec1, vec2):
    """
    calculates cosine similarity
    """
    dict2 = dict(vec2)
    prods = (count*dict2[wid] for wid, count in vec1 if wid in dict2)
    numerator = 1.0 * sum(prods)
    denominator = 1.0 * l2norm(vec1) * l2norm(vec2)
    return numerator / denominator





def indices_decorator(tables=[]):
    """
    create a decorator that:
      drops indices
      runs the function
      re-creates indices

    NOTE: It loses your constraints!
    """
    if tables == None:
        tables = []
        
    WHERE = ["schemaname = 'public'"]
    ORWHERE = []
    for table in tables:
        ORWHERE.append("tablename = %s")
    ORWHERE = ' or '.join(ORWHERE)
    WHERE.append(ORWHERE)
    WHERE = ' and '.join(WHERE)



    @transaction.commit_manually
    def manage_indices(load_f):
        def retf():
            cur = connection.cursor()
            sql = "select tablename, indexname, indexdef from pg_indexes where %s" % WHERE
            cur.execute(sql, tuple(tables))
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
    return manage_indices



def copy_to_table(table, cols, fname):
    abspath = os.path.abspath(fname)

    @transaction.commit_manually
    @indices_decorator([table])
    def load_db():
        fields = ['yid', 'word', 'count', 'score']
        query = "COPY %s (%s) FROM STDIN WITH CSV;" % (table, ", ".join(cols))
        cmd = "cat %s | psql -c \"%s\" confo confo" % (abspath, query)
        os.system(cmd)

    return load_db

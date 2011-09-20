import os
import sys
import time

ROOT = os.path.abspath('%s/../..' % os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = 'confo.settings'
from django.core.management import setup_environ
from confo import settings
setup_environ(settings)
from confo.home.models import *
from django.db import connection, transaction
from django.db.models import *

TMPFILE = "__cluster__tmp.txt"

class UniqueIder:
    def __init__(self):
        self.__id = 0
        self.__map = {}
    def getid(self, key):
        try:
            retval = self.__map[key]
        except:
            self.__id += 1
            retval = self.__id
            self.__map[key] = self.__id
        return retval

class Clusterer:
    def __init__(self, table_getter, table_clearer, from_key, to_key, query, topn, vector_size, unique_words_max, clusterpython):
        self.table_getter = table_getter
        self.table_clearer = table_clearer
        self.query = query
        self.topn = topn
        self.vector_size = vector_size
        self.unique_words_max = unique_words_max
        self.from_key = from_key
        self.to_key = to_key
        self.clusterpython = clusterpython

    def dump_query(self, cur):
        outfile = open(TMPFILE, "w")
        print "Executing count query, outputting file", time.time()
        cur.execute(self.query)
        ider = UniqueIder()
        for iid, term, count in cur:
            wid = ider.getid(term)
            outfile.write("%d,%d,%d\n" % (iid, wid, count))
        outfile.close()

    def load_similar(self, cur):
        print "Loading file into similar conferences table", time.time()
        read_table = self.table_getter("r")
        read_table.logtodb(cur)
    
    def run_clustering(self):
        tbl = self.table_getter("r")
        cmd = "%s clustering_part2.py %s %s %s %s %s %s %d %d %d" % (self.clusterpython, TMPFILE, ",".join(tbl.props), tbl.logname, tbl.tablename, self.from_key, self.to_key, self.topn, self.vector_size, self.unique_words_max)
        os.system(cmd)

    @transaction.commit_on_success
    def build_similar(self):
        print "start time", time.time()
        cur = connection.cursor()
#        self.dump_query(cur)
        self.run_clustering()
        self.table_clearer()
        transaction.commit()
        self.load_similar(cur)
        print "end time", time.time()

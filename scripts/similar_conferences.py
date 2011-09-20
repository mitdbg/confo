from clustering import Clusterer
from confo.home.models import *
from dblogging import LogOrCache
import sys

TOPN = 10
VECTOR_SIZE = 20
UNIQUE_WORDS_MAX = 300

def get_table(mode):
    return LogOrCache(["fromconf","toconf","similarity"], "similar_conferences.txt", mode, "similar_conferences")

def clear_table():
    SimilarConferences.objects.all().delete()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "argument: path_to_clustering_python_bin"
        sys.exit(-1)
    q = """select y.cid, ywc.word, sum(ywc.count) AS total
           from years as y, year_word_counts as ywc
           where y.id = ywc.yid
           group by y.cid, ywc.word
           order by y.cid, total DESC;"""
    c = Clusterer(get_table, clear_table, 'fromconf', 'toconf', q, TOPN, VECTOR_SIZE, UNIQUE_WORDS_MAX, sys.argv[1])
    c.build_similar()

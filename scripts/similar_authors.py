from clustering import Clusterer
from confo.home.models import *
from dblogging import LogOrCache
import sys

TOPN = 10
VECTOR_SIZE = 20
UNIQUE_WORDS_MAX = 2500

def get_table(mode):
    return LogOrCache(["fromauth","toauth","similarity"], "similar_authors.txt", mode, "similar_authors")

def clear_table():
    SimilarAuthors.objects.all().delete()    

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "argument: path_to_clustering_python_bin"
        sys.exit(-1)
    q = """SELECT pa.author_id, w.word, count(*) AS total
           from words as w, papers_authors as pa
           where pa.paper_id = w.pid
           group by pa.author_id, w.word
           order by pa.author_id, total DESC;"""
    c = Clusterer(get_table, clear_table, 'fromauth', 'toauth', q, TOPN, VECTOR_SIZE, UNIQUE_WORDS_MAX, sys.argv[1])
    c.build_similar()

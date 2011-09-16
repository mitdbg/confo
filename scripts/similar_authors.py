from clustering import Clusterer
from confo.home.models import *
from dblogging import LogOrCache

TOPN = 10
VECTOR_SIZE = 20
UNIQUE_FRAC = .002

def get_table(mode):
    return LogOrCache(["fromauth","toauth","similarity"], "similar_authors.txt", mode, "similar_authors")

def clear_table():
    SimilarAuthors.objects.all().delete()    

if __name__ == '__main__':
    q = """SELECT pa.author_id, w.word, count(*) AS total
           from words as w, papers_authors as pa
           where pa.paper_id = w.pid
           group by pa.author_id, w.word
           order by pa.author_id, total DESC;"""
    c = Clusterer(get_table, clear_table, q, TOPN, VECTOR_SIZE, UNIQUE_FRAC)
    c.build_similar()

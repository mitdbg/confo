from clustering import Clusterer
from confo.home.models import *
from dblogging import LogOrCache

TOPN = 10
VECTOR_SIZE = 20
UNIQUE_FRAC = .05

def get_table(mode):
    return LogOrCache(["fromconf","toconf","similarity"], "similar_conferences.txt", mode, "similar_conferences")

def clear_table():
    SimilarConferences.objects.all().delete()

if __name__ == '__main__':
    q = """select y.cid, ywc.word, sum(ywc.count) AS total
           from years as y, year_word_counts as ywc
           where y.id = ywc.yid
           group by y.cid, ywc.word
           order by y.cid, total DESC;"""
    c = Clusterer(get_table, clear_table, q, TOPN, VECTOR_SIZE, UNIQUE_FRAC)
    c.build_similar()

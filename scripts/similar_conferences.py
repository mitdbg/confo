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
from django.db.models import *

from dblogging import load_logger
from operator import attrgetter

TOPN = 10

def conf_words(cur):
    confs = {}
    words = {}
    for cid, wid, count in cur:
        conf = confs.get(cid, [])
        conf.append((wid, count))
        if len(conf) == 1:
            confs[cid] = conf

        word = words.get(wid, set())
        word.add(cid)     
        if len(word) == 1:
            words[wid] = word
    return (confs, words)

def similarity(vec1, vec2):
    dict2 = dict(vec2)
    prods = (count*dict2[wid] for wid, count in vec1 if wid in dict2)
    return reduce(lambda x,y: x+y, prods)

def topn_similar(cid, vector, candidates, conf_words):
    similar = []
    for cand in candidates:
        cand_vector = conf_words[cand]
        sim = similarity(vector, cand_vector)
        sc = SimilarConferences(fromconf=cid, toconf=cand, similarity=sim)
        similar.append(sc)
    
    sort_sim = sorted(similar, key=attrgetter('similarity'), reverse=True)
    keepers = sort_sim[:TOPN]
    for keeper in keepers:
        keeper.save()

@transaction.commit_on_success
def similar_conferences():
    SimilarConferences.objects.all().delete()

    cur = connection.cursor()
    print "Getting conference counts"
    q = """select y.cid, w.id, sum(ywc.count)
           from years as y, year_word_counts as ywc, words as w
           where y.id = ywc.yid AND w.word = ywc.word
           group by y.cid, w.id;"""
    cur.execute(q)
    conf_words, word_confs = confs_words(cur)
    print "Calculating similarities"
    for cid, vector in confs.items():
        cand_sets = [word_confs[wid] for wid, count in vector]
        candidates = reduce(lambda x, y: x | y, cand_sets)
        topn_similar(cid, vector, candidates, conf_words)

if __name__ == '__main__':
    similar_conferences()

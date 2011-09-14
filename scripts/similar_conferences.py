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

from dblogging import LogOrCache
from operator import itemgetter

TOPN = 10

def confs_words(cur):
    print "Getting conference counts"
    q = """select y.cid, w.id, sum(ywc.count)
           from years as y, year_word_counts as ywc, words as w
           where y.id = ywc.yid AND w.word = ywc.word
           group by y.cid, w.id;"""
    cur.execute(q)
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

def l2norm(vec):
    sum_squares = sum(count*count for wid, count in vec)
    return sqrt(sum_squares)

def similarity(vec1, vec2):
    dict2 = dict(vec2)
    prods = (count*dict2[wid] for wid, count in vec1 if wid in dict2)
    numerator = 1.0 * sum(prods)
    denominator = 1.0 * l2norm(vec1) * l2norm(vec2)
    return numerator / denominator

def calc_similarities(cid, vector, candidates, conf_words):
    similar = []
    for cand in candidates:
        cand_vector = conf_words[cand]
        sim = similarity(vector, cand_vector)
        sc = {'fromconf': cid, 'toconf': cand, 'similarity': sim}
        similar.append(sc)
    return similar

def write_topn(similar, table):
    sort_sim = sorted(similar, key=itemgetter('similarity'), reverse=True)
    keepers = sort_sim[:TOPN]
    for keeper in keepers:
        table.get(None, keeper, False)

def get_table(mode):
    return LogOrCache(["fromconf","toconf","similarity"], "similar_conferences.txt", mode, "similar_conferences")

def write_similar(conf_words, word_confs):
    print "Calculating similarities, writing to file"
    write_table = get_table("w")
    for cid, vector in conf_words.items():
        cand_sets = [word_confs[wid] for wid, count in vector]
        candidates = reduce(lambda x, y: x | y, cand_sets)
        similar = calc_similarities(cid, vector, candidates, conf_words)
        write_topn(similar, write_table)
    write_table.close()

def load_similar(cur):
    print "Loading file into similar conferences table"
    read_table = get_table("r")
    read_table.logtodb(cur)

@transaction.commit_on_success
def similar_conferences():
    cur = connection.cursor()
    conf_words, word_confs = confs_words(cur)
    write_similar(conf_words, word_confs)
#    load_similar(cur)

if __name__ == '__main__':
    similar_conferences()

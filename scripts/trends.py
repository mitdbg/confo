import os
import sys
from util import similarity
import nltk
from nltk.corpus import stopwords

ROOT = os.path.abspath('%s/../..' % os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = 'confo.settings'
from django.core.management import setup_environ
from confo import settings
setup_environ(settings)
from confo.home.models import *
from django.db import connection, transaction


# for every conference year, get the counts of top 20
@transaction.commit_manually
def get_conf_terms():
    cur = connection.cursor()
    sql = """select yid, word, tfidf
             from year_tfidf as t order by yid asc, tfidf desc;"""
    cur.execute(sql)
    curyid = None
    d = {}
    wtoy = {}
    for yid, word, c in cur:
        if curyid != yid:
            curl = d[yid] = []
            curyid = yid
        if len(curl) < 20:
            curl.append((word, c))

        s = wtoy.get(word, set())
        s.add(yid)
        wtoy[word] = s
            
    return d, wtoy


# for every paper, extract the terms
@transaction.commit_manually
def get_paper_terms():
    cur = connection.cursor()
    cur.execute("select pid, word, c from papers_word_counts order by pid, c desc;")
    curpid = None
    d = {}
    w_to_pid = {}
    for pid, word, c in cur:
        if curpid != pid:
            curl = d[pid] = []
            curpid = pid
        if len(curl) < 20:
            curl.append((word, c))

        s = w_to_pid.get(word, set())
        s.add(pid)
        w_to_pid[word] = s

    return d, w_to_pid


if __name__ == "__main__":
    print >> sys.stderr, "loading conference years"
    ytow, wtoy = get_conf_terms()
    print >> sys.stderr, "loading paper word counts"
    ptow, wtop = get_paper_terms()
    print >> sys.stderr, "Calculating cosines! Gonna get 'er done!"

    totallen = len(ytow)
    idx = 0

    for y, ywcounts in ytow.items():
        # gather all relevant publications
        pids = set()
        for w, c in ywcounts:
            pids.update(wtop.get(w,[]))

        # for each publication, calculate cosine
        scores = []
        for pid in pids:
            pwcounts = ptow[pid]

            scores.append((pid, similarity(ywcounts, pwcounts)))

        scores.sort(key=lambda x: x[1], reverse=True)
        for pid, score in scores[:20]:
            print "%d,%d,%f" % (y,pid,score)

        idx += 1




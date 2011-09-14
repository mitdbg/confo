import math
import os
import sys
import numpy as np

ROOT = os.path.abspath('%s/../..' % os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = 'confo.settings'
from django.core.management import setup_environ
from confo import settings
setup_environ(settings)
from confo.home.models import *
from django.db import connection, transaction




def get_idf(cid, yids):
    cur = connection.cursor()
    if len(yids) == 0:
        print >> sys.stderr, "%d had no years" % cid
    idfq = """select word, count(count), sum(count) as s
              from years, year_word_counts as ywc where years.cid = %s and ywc.yid = years.id group by word;"""
    cur.execute(idfq, (cid,))
    idfs = {}
    for word, c, s in cur:
        idf = math.log(float(len(yids)) / (float(c)), 10)
        idfs[word] = idf
        if idf == 0:
            print >> sys.stderr, "%d\t%s\t%d\t%d\t%f" % (cid, word, len(yids), c, idf)
    return idfs

def get_tf_by_y(cid):
    cur = connection.cursor()    
    tfq = """select years.id, word, sum(count)
             from years, year_word_counts as ywc
             where years.cid = %s and ywc.yid = years.id group by years.id, word order by years.id"""
    cur.execute(tfq, (cid, ))
    tfs_by_y = {}
    for year, word, s in cur:
        tfs = tfs_by_y.get(year, {})
        tfs[word] = float(s)
        tfs_by_y[year] = tfs
    return tfs_by_y


if __name__ == '__main__':
    # get all conference years
    cur = connection.cursor()
    cur.execute("select cid, id from years order by cid, id asc")
    d = {}
    for cid, year in cur:
        l = d.get(cid, [])
        l.append(year)
        d[cid ] = l


    
    fidf = file("idf.txt",'w')
    ftfidf = file('tfidfetxt', 'w')

    for cid, yids in d.items():
        idfs = get_idf(cid, yids)
        idfs_ordered = sorted(idfs.items(), key=lambda x:x[1])
        avg = np.mean(map(lambda x:x[1], idfs_ordered))
        std = np.std(map(lambda x:x[1], idfs_ordered))
        #idfs_ordered = filter(lambda x: x[1] < (avg - std), idfs_ordered)
        for word, idf in idfs_ordered:
            fidf.write("%d,%s,%f\n" % (cid, word, idf))

        tfs_by_y = get_tf_by_y(cid)
        for yid in yids:
            tfs = tfs_by_y.get(yid,{})
            stats = []
            for word, idf in idfs.items():
                stats.append((word, idf * tfs.get(word,0)))
            stats = filter(lambda x: x[1] != 0, stats)
            stats.sort(key=lambda x:x[1], reverse=True)
            for word, tfidf in stats:
                ftfidf.write("%d,%s,%d,%f\n" % (yid, word, tfs.get(word,0), tfidf))

    fidf.close()
    ftfidf.close()


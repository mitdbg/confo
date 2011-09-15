import os
import sys
from util import *

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



@transaction.commit_on_success
def top_conferences():
    ret = ConfYear.objects.aggregate(Min('year'), Max('year'))
    years = range(ret['year__min'],ret['year__max'] + 1)

    cur = connection.cursor()
    q = """select y.cid, y.year, count(*)
    from years as y, papers as p
    where p.cid = y.id group by y.cid, y.year  order by y.cid, y.year;"""
    cur.execute(q)

    data = {}
    for cid, year, n in cur:
        if cid not in data:
            data[cid] = {}
        data[cid][year] = n

    for conf in Conference.objects.all():
        d = data[conf.pk]
        counts = [d.get(year, 0) for year in years]
        conf.counts.yearcounts = ','.join(map(str,counts))
        conf.counts.save()


def first_papers():
    c = connection.cursor()
    print "loading words->pid"
    c.execute("select word, pid from words")
    wtop = {}
    for w, p in c:
        ps = wtop.get(w,set())
        ps.add(p)
        wtop[w]=ps

    print "loading cid->pid->yid"
    c.execute("select y.cid, p.id, y.year from papers as p, years as y where p.cid = y.id")
    ctoptoy = {}
    for cid, pid, year in c:
        if cid not in ctoptoy: ctoptoy[cid] = {}
        ctoptoy[cid][pid] = year

    print "leading cid->word"
    sql = """select c.id, ci.word
             from conferences as c, conf_idf as ci
             where ci.cid = c.id order by c.id, ci.idf"""
    c.execute(sql)
    f = file("first_papers.txt", 'w')

    print "writing data out"
    prevcid = None
    n = 0
    for cid, word in c:

        ptoy = ctoptoy[cid]

        pbyy = [(pid, ptoy[pid]) for pid in wtop.get(word,[]) if pid in ptoy]
        pbyy.sort(key=lambda x: x[1])
        if len(pbyy):
            pid, year = pbyy[0]
            print >>f, "%d,%d,%s" % (cid, pid, word)
    f.close()

    print "copying to database"
    load_db = copy_to_table('first_papers', ['cid', 'pid', 'word'], './first_papers.txt')
    load_db()
    
    

    
if __name__ == '__main__':
    top_conferences()

    first_papers()
    

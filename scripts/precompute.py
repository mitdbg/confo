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



@transaction.commit_manually
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
        counts = data.get(cid, {})
        counts[year] = n
        data[cid] = counts
    try:
        for conf in Conference.objects.all():

            if not conf.counts.yearcounts == '':
                d = data[conf.pk]
                counts = [d.get(year, 0) for y in years]
                conf.counts.yearcounts = ','.join(map(str,counts))
                conf.counts.save()
        transaction.commit()
    except:
        transaction.rollback()

    
if __name__ == '__main__':
    os.system('psql -f ./setup.sql confo confo')
    top_conferences()

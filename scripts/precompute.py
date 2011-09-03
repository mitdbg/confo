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




def top_conferences():
    cs = Conference.objects.annotate(c=Count('confyear__paper'),
                                minyear=Min('confyear__year'),
                                maxyear=Max('confyear__year')).order_by('-c')

    ret = ConfYear.objects.aggregate(Min('year'), Max('year'))
    years = range(ret['year__min'],ret['year__max'] + 1)
    
    for conf in cs:
        try:
            conf.counts
        except:
            cys = ConfYear.objects.filter(conf=conf).annotate(c=Count('paper'))
            d = dict([(cy.year, cy.c) for cy in cys])
            counts = [d.get(y, 0) for y in years]
            yearcounts = ','.join(map(str, counts))
            cc = ConferenceCounts(conf=conf, count=conf.c,
                                  minyear=conf.minyear, maxyear=conf.maxyear,
                                  yearcounts=yearcounts)
            cc.save()

@transaction.commit_manually
def author_counts():
    if Author.objects.filter(pubcount__gt=10).count() > 0: return
    auths = Author.objects.annotate(c=Count('papers')).filter(c__gt=10).order_by('-c')
    for auth in auths:
        print '%d,%d' % (auth.pk,auth.c)
        auth.pubcount = auth.c
        auth.save()
    transaction.commit()
    
if __name__ == '__main__':
    author_counts()
    top_conferences()

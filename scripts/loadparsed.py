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
from dblogging import load_logger

@transaction.commit_manually
def load_db():
    try:
        (confcache, confycache, authcache, papercache, pacache) = load_logger("r")
        cursor = connection.cursor()
        confcache.logtodb(cursor, "conferences")
        confycache.logtodb(cursor, "years")
        papercache.logtodb(cursor, "papers")
        authcache.logtodb(cursor, "authors")
        pacache.logtodb(cursor, "papers_authors")
        transaction.commit()
    except Exception, e:
        transaction.rollback()
        raise

if __name__ == '__main__':
    load_db()

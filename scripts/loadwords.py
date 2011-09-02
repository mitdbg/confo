import os
import sys
import nltk
import sqlite3
from nltk.corpus import stopwords

ROOT = os.path.abspath('%s/../..' % os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = 'confo.settings'
from django.core.management import setup_environ
from confo import settings
setup_environ(settings)
from confo.home.models import *
from django.db import connection, transaction

@transaction.commit_manually
def load_db():
    try:
        cursor = connection.cursor()
        f = file('./allwords.txt', 'r')
        cursor.copy_from(f, 'words', columns=('pid','word'), sep=',' )
        transaction.commit()
    except Exeption, e:
        transaction.rollback()
        raise

if __name__ == '__main__':
    load_db()

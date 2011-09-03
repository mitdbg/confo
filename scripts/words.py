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



stemmer = nltk.stem.porter.PorterStemmer()
stop = set(stopwords.words('english'))
stop.update(['use', 'using', 'used'])
table = ''.join(map(chr, range(256))) # translation table
stripchars = '- \t'
badchars = '\'"().,:; \t?!@'



def words_from_title(title):
    words = [str(word).strip(stripchars).translate(table, badchars)
             for word in title.split()]
    words = map(lambda word: word.lower(), words)
    words = set(filter(lambda word: word not in stop, words))
    return words

def get_title_iter():
    for paper in Paper.objects.all():
        yield paper

def extract_words(allstems):
    allstems = allstems
    for paper in get_title_iter():
        tid, title = paper.pk, paper.title
        words = words_from_title(title)
        stems = map(stemmer.stem, words)
        words = filter(lambda stem:stem, map(lambda stem: allstems.get(stem,None), stems))
        if tid % 10000 == 0: print tid
        for word in words:
            yield tid, word
        
    


if __name__ == '__main__':
    from django.db import connection, transaction


    f = file('./stems.txt', 'r')
    allstems = {}
    for l in f:
        k,v = tuple(l.strip().split(','))
        allstems[k] = v
    f.close()


    print "writing out words"
    f = file('./allwords.txt', 'w')
    for tid, word in extract_words(allstems):
        print >> f, '%d,%s' % (tid, word)
    f.close()

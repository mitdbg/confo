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

badchars = '\'"().,:;- \t'

def words_from_title(title):
    words = [word.strip(badchars).strip() for word in title.strip().split()]
    words = set(map(lambda word: word.lower(), words))
    words = filter(lambda word: word not in stop, words)
    return words

def extract_words(allstems):
    allstems = allstems
    for paper in get_title_iter():
        tid, title = paper.pk, paper.title
        words = words_from_title(title)
        stems = map(stemmer.stem, words)
        words = filter(lambda stem:stem, map(lambda stem: allstems.get(stem,None), stems))

        for word in words:
            yield tid, word
        

def collect_stem_mappings():
    allstems = {}
    
    for paper in get_title_iter():
        tid, title = paper.pk, paper.title
        words = words_from_title(title)

        for word in words:

            stem = stemmer.stem(word)
            if stem not in allstems:
                allstems[stem] = word
            else:
                if len(word) < allstems[stem]:
                    allstems[stem] = word
    return allstems
    
def get_title_iter():
    for paper in Paper.objects.all():
        yield paper
    


if __name__ == '__main__':
    from django.db import connection, transaction
    print "extracting words from titles"
    allstems = collect_stem_mappings()


    f = file('./allwords.txt', 'w')
    for tid, word in extract_words(allstems):
        print >> f, '%d,%s' % (tid, word)
    f.close()

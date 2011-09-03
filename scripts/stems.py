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
stripchars = '-'
badchars = '\'"().,:; \t?!@'



def collect_stem_mappings():
    allstems = {}
    seenwords = set()
    for paper in get_title_iter():
        tid, title = paper.pk, paper.title
        words = words_from_title(title)

        for word in words:
            if word in seenwords: continue
            seenwords.add(word)
            
            stem = stemmer.stem(word)
            if stem:
                d = allstems.get(stem, {})
                d[word] = d.get(word,0) + 1
                allstems[stem] = d
        if tid % 10000 == 0: print tid

    allstems = dict([(key, max(d.items(), key=lambda p:p[1])[0])
                     for key,d in allstems.items()
                     if sum(d.values()) > 2])

    return allstems
    

def words_from_title(title):
    words = [str(word).strip(stripchars).translate(table, badchars)
             for word in title.strip().split()]
    words = set(map(lambda word: word.lower(), words))
    words = filter(lambda word: word not in stop, words)
    return words

def get_title_iter():
    for paper in Paper.objects.all():
        yield paper



if __name__ == '__main__':
    from django.db import connection, transaction
    print "extracting words from titles"
    allstems = collect_stem_mappings()

    print "writing out stems"
    f = file('./stems.txt', 'w')
    for stem, word in allstems.items():
        print >> f, ','.join([stem,word])
    f.close()

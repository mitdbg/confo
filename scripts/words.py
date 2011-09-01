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
print settings.DATABASES
from confo.home.models import *



stemmer = nltk.stem.porter.PorterStemmer()
stop = set(stopwords.words('english'))
stop.update(['use', 'using', 'used'])


badchars = '\'"().,:;- \t'

def words_from_title(title):
    words = [word.strip(badchars).strip() for word in title.strip().split()]
    words = filter(lambda word: word not in stop, words)
    words = set(map(lambda word: word.lower(), words))
    return words



class Extractor(object):
    def __init__(self,allstems):
        self.allstems = allstems
        self.size = Paper.objects.all().count()
    def __iter__(self):

        allstems = self.allstems
        for paper in get_title_iter():
            tid, title = paper.pk, paper.title
            words = words_from_title(title)
            stems = map(stemmer.stem, words)
            words = filter(lambda stem:stem, map(lambda stem: allstems.get(stem,None), stems))

            print title, "\t", words
            for word in words:
                yield tid, word
        
    def __len__(self):
        return self.size

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
    print allstems
    return allstems
    
def get_title_iter():
    # ps = Paper.objects.all()
    # yield ps[len(ps)-1]
    # return
    for paper in Paper.objects.all():
        yield paper
    # cur = conn.cursor()
    # cur.execute("select id, title from titles")
    # for row in cur:
    #     yield row
    # cur.close()
    


if __name__ == '__main__':
    from django.db import connection, transaction
    allstems = collect_stem_mappings()
    extractor = Extractor(allstems)
    cursor = connection.cursor()
    cursor.executemany("insert into words (pid,word) values (?,?)",  extractor)
    transaction.commit_unless_managed()
    

    #conn.commit()
    #cur.close()

import os
import sys
import time
from util import similarity

ROOT = os.path.abspath('%s/../..' % os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = 'confo.settings'
from django.core.management import setup_environ
from confo import settings
setup_environ(settings)
from confo.home.models import *
from django.db import connection, transaction
from django.db.models import *
from multiprocessing import Pool
from operator import itemgetter

counts = {}
invert = {}
banned = set()

class UniqueIder:
    def __init__(self):
        self.__id = 0
        self.__map = {}
    def getid(self, key):
        try:
            retval = self.__map[key]
        except:
            self.__id += 1
            retval = self.__id
            self.__map[key] = self.__id
        return retval

def calc_similarities(arg):
    (cid, vector, from_key, to_key, topn) = arg
    cand_sets = [invert[wid] for wid, count in vector if wid not in banned]
    similar = []
    if len(cand_sets) > 0:
        candidates = reduce(lambda x, y: x | y, cand_sets)
        for cand in candidates:
            if cid != cand:
                cand_vector = counts[cand]
                sim = similarity(vector, cand_vector)
                sc = {from_key: cid, to_key: cand, 'similarity': sim}
                similar.append(sc)
    if cid % 1000 == 0:
        print "calculated ", cid, time.time()
    sort_sim = sorted(similar, key=itemgetter('similarity'), reverse=True)
    return sort_sim[:topn]

class Clusterer:
    def __init__(self, table_getter, table_clearer, from_key, to_key, query, topn, vector_size, unique_words_max):
        self.table_getter = table_getter
        self.table_clearer = table_clearer
        self.query = query
        self.topn = topn
        self.vector_size = vector_size
        self.unique_words_max = unique_words_max
        self.from_key = from_key
        self.to_key = to_key

    def count_and_index(self, cur):
        global counts
        global invert
        print "Executing count query", time.time()
        cur.execute(self.query)
        print "Query executed, generating vectors and inverted index", time.time()
        ider = UniqueIder()
        cur_item = -1
        item_term_count = 0
        for iid, term, count in cur:
            wid = ider.getid(term)
            if cur_item == iid and item_term_count == self.vector_size:
                continue
            if cur_item != iid:
                cur_item = iid
                item_term_count = 0
            item_term_count += 1
            if wid in banned:
                continue
            item_count = counts.get(iid, [])
            if len(item_count) == self.vector_size:
                continue
            item_count.append((wid, float(count)))
            if len(item_count) == 1:
                if len(counts) % 1000 == 0:
                    print "loaded ", len(counts), time.time()
                counts[iid] = item_count

            word = invert.get(wid, set())
            word.add(iid)     
            if len(word) == 1:
                invert[wid] = word
            if len(word) >= self.unique_words_max:
                banned.add(wid)
                del invert[wid]
    
    def work_generator(self):
        for cid, vector in counts.items():
            yield cid, vector, self.from_key, self.to_key, self.topn

    def write_similar(self):
        print "Calculating similarities, writing to file", time.time()
        similar_pool = Pool(processes=14)
        it = similar_pool.imap(calc_similarities, self.work_generator(), 1000)
        write_table = self.table_getter("w")
        for keepers in it:
            for keeper in keepers:
                write_table.get(None, keeper, False)
        write_table.close()

    def load_similar(self, cur):
        print "Loading file into similar conferences table", time.time()
        read_table = self.table_getter("r")
        read_table.logtodb(cur)

    @transaction.commit_on_success
    def build_similar(self):
        print "start time", time.time()
        cur = connection.cursor()
        self.count_and_index(cur)
        self.write_similar()
        self.table_clearer()
        transaction.commit()
        self.load_similar(cur)
        print "end time", time.time()

import os
import sys
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

from operator import itemgetter

class Clusterer:
    def __init__(self, table_getter, query, topn, vector_size, unique_frac):
        self.table_getter = table_getter
        self.query = query
        self.topn = topn
        self.vector_size = vector_size
        self.unique_frac = unique_frac

    def count_and_index(self, cur):
        print "Executing count query"
        cur.execute(self.query)
        print "Query executed, generating vectors and inverted index"
        counts = {}
        invert = {}
        for iid, wid, count in cur:
            item_count = counts.get(iid, [])
            if len(item_count) == self.vector_size:
                continue
            item_count.append((wid, float(count)))
            if len(item_count) == 1:
                counts[iid] = item_count

            word = invert.get(wid, set())
            word.add(iid)     
            if len(word) == 1:
                invert[wid] = word
        return (counts, invert)

    def calc_similarities(self, cid, vector, candidates, counts):
        similar = []
        for cand in candidates:
            if cid != cand:
                cand_vector = counts[cand]
                sim = similarity(vector, cand_vector)
                sc = {'fromconf': cid, 'toconf': cand, 'similarity': sim}
                similar.append(sc)
        return similar

    def write_topn(self, similar, table):
        sort_sim = sorted(similar, key=itemgetter('similarity'), reverse=True)
        keepers = sort_sim[:self.topn]
        for keeper in keepers:
            table.get(None, keeper, False)

    def write_similar(self, counts, invert):
        print "Calculating similarities, writing to file"
        write_table = self.table_getter("w")
        for cid, vector in counts.items():
            cand_sets = [invert[wid] for wid, count in vector]
            cand_sets = filter(lambda x: len(x) < self.unique_frac * len(counts), cand_sets)
            if len(cand_sets) > 0:
                candidates = reduce(lambda x, y: x | y, cand_sets)
                similar = self.calc_similarities(cid, vector, candidates, counts)
                self.write_topn(similar, write_table)
        write_table.close()

    def load_similar(self, cur):
        print "Loading file into similar conferences table"
        read_table = self.table_getter("r")
        read_table.logtodb(cur)

    @transaction.commit_on_success
    def build_similar(self):
        cur = connection.cursor()
        counts, invert = self.count_and_index(cur)
        self.write_similar(counts, invert)
        transaction.commit()
        self.load_similar(cur)

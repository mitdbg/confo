from multiprocessing import Pool
from operator import itemgetter
from dblogging import LogOrCache
from math import sqrt

import sys
import time

counts = {}
invert = {}
banned = set()

def l2norm(vec):
    sum_squares = sum(count*count for wid, count in vec)
    return sqrt(sum_squares)

def similarity(vec1, vec2):
    dict2 = dict(vec2)
    prods = (count*dict2[wid] for wid, count in vec1 if wid in dict2)
    numerator = 1.0 * float(sum(prods))
    denominator = 1.0 * l2norm(vec1) * l2norm(vec2) + 1.0
    return numerator / denominator

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
#    return sort_sim[0]
    return sort_sim[:topn]
    
class Clusterer:
    def __init__(self, infilename, logfile, from_key, to_key, topn, vector_size, unique_words_max):
        self.infile = open(infilename, "r")
        self.logfile = logfile
        self.topn = topn
        self.vector_size = vector_size
        self.unique_words_max = unique_words_max
        self.from_key = from_key
        self.to_key = to_key
    def count_and_index(self):
        global counts
        global invert
        global banned

        print "Generating vectors and inverted index", time.time()
        cur_item = -1
        item_term_count = 0
        for line in self.infile:
            parts = line.split(",")
            (iid, wid, count) = (int(parts[0]), int(parts[1]), float(parts[2]))
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
        similar_pool = Pool(processes=10)
        it = similar_pool.imap(calc_similarities, self.work_generator(), 1000)
        for keepers in it:
            for keeper in keepers:
                self.logfile.get(None, keeper, False)
        self.logfile.close()

if __name__ == "__main__":
    (infilename, props, outfilename, tablename, from_key, to_key, topn, vector_size, unique_words_max) = sys.argv[1:]
    log = LogOrCache(props.split(",")[1:], outfilename, "w", tablename)
    c = Clusterer(infilename, log, from_key, to_key, int(topn), int(vector_size), int(unique_words_max))
    c.count_and_index()
    c.write_similar()

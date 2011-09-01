import sys
import nltk
import sqlite3
from nltk.corpus import stopwords


stemmer = nltk.stem.porter.PorterStemmer()
stop = set(stopwords.words('english'))
badchars = '.,:;- \t'

def extract_words(allstems, conn):
    """
    two passes,
    first pass calculates stem->shortest word mapping
    second pass calculates words for each title and inserts into database
    """


    for tid, title in get_title_iter(conn):
        words = [word.strip(badchars) title.strip().split()]
        words = filter(lambda word: word not in stop, words)
        words = set(map(lambda word: word.lower, words))
        words = filter(lambda word:word, map(lambda word: allstems.get(word,None), words))

        for word in words:
            yield tid, word

def collect_stem_mappings(conn):
    allstems = {}
    
    for tid, title in get_title_iter(conn):
        words = [word.strip(badchars) title.strip().split()]
        words = filter(lambda word: word not in stop, words)
        words = map(lambda word: word.lower, words)

        for word in words:
            stem = stemmer.stem(word)
            if stem not in allstems:
                allstems[stem] = word
            else:
                if len(word) < allstems[stem]:
                    allstems[stem] = word
    return allstems
    
def get_title_iter(conn):
    cur = conn.cursor()
    cur.execute("select id, title from titles")
    for row in cur:
        yield row
    cur.close()
    


if __name__ == '__main__':
    allstems = collect_stem_mappings(conn)
    conn = sqlite3
    cur = conn.cursor()
    cur.executemany("insert into words values (?,?)",  extract_words(allstems, conn))
    conn.commit()
    cur.close()

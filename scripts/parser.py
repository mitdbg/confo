import sys, os
from nltk.corpus import stopwords
from dblogging import load_logger
import xml.parsers.expat
import time


ROOT = os.path.abspath('%s/../..' % os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = 'confo.settings'
from django.core.management import setup_environ
from confo import settings
setup_environ(settings)

from confo.home.models import *
from django.db import connection, transaction

(confcache, confycache, authcache, papercache, pacache) = load_logger("w")

class FormatError(Exception):
    def __init__(self, message):
        self.message = message


paperinfo = None
curkey = None
stop = set(stopwords.words('english'))
counter = 0
MAXCOUNTER = 200500000

def get_conf(crossref):
    parts = crossref.split("/")
    if parts != "conf" and len(parts) < 2:
        raise FormatError("crossref '%s' was unexpected" % crossref)
    return parts[1]

def process_paper(paperinfo):
    year = int(paperinfo["year"][0])
    title = paperinfo["title"][0]
    conf = get_conf(paperinfo.get("crossref", [""])[0])
    confname = paperinfo["booktitle"][0]
    authors = paperinfo.get("author", [])

    if year < 1910 or year > 2020:
        raise FormatError("bad paper year")
        return

    auths = [authcache.get(author, {'name':author}, True) for author in authors]
    return
    c = confcache.get(conf, {'short':conf, 'name':confname}, True)
    y = confycache.get(conf+str(year), {'cid': c, 'year': year}, True)


    try:
        p = papercache.get("", {'cid':y, 'title': title}, False)
        for auth in auths:
            pa = pacache.get("", {'paper_id':p, 'author_id': auth}, False)
    except:
        raise FormatError("error building paper")

def dump_paperauths():
    cursor = connection.cursor()
    paperauths = file(PAPERAUTHS, "r")
    cursor.copy_from(paperauths, 'papers_authors', columns=('paper_id','author_id'), sep=',' )
    paperauths.close()

@transaction.commit_manually    
def parse(filename):
    storekeys = set(("year", "title", "author", "crossref", 'booktitle'))

    def start_element(name, attrs):
        global paperinfo, curkey
        if name == "inproceedings":
            paperinfo = {}
        elif paperinfo != None and name in storekeys:
            curkey = name
    def end_element(name):
        global paperinfo, curkey, counter
        try:
            if paperinfo != None and name == "inproceedings":
                if counter < MAXCOUNTER:
                    process_paper(paperinfo)
                paperinfo = None
                counter += 1
                if counter % 10000 == 0:
                    print counter, time.time()
        except FormatError,  e:
            sys.stderr.write("Formatting exception: %s on %s\n" % (e.message, repr(paperinfo)))
            
    def char_data(data):
        global paperinfo, curkey

        if curkey != None:
            if 'author' == curkey and 'Eugene Wu' in data:
                print data
            vals = paperinfo.get(curkey, [])
            vals.append(data)
            paperinfo[curkey] = vals
            curkey = None
    try:
        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = start_element
        p.EndElementHandler = end_element
        p.CharacterDataHandler = char_data
        p.ParseFile(open(filename))
#        dump_paperauths()
        transaction.commit()
    except Exception, e:
        print "in exception"
        transaction.rollback()
        raise

if __name__ == "__main__":
    print "parsing dblp.xml"
    fname = len(sys.argv) > 1 and sys.argv[1] or 'dblp.xml'
    parse(fname)


import sys, os
from nltk.corpus import stopwords
import xml.parsers.expat

ROOT = os.path.abspath('%s/../..' % os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = 'confo.settings'
from django.core.management import setup_environ
from confo import settings
setup_environ(settings)

from confo.home.models import *
from django.db import transaction

paperinfo = None
curkey = None
stop = set(stopwords.words('english'))
counter = 0


class FormatError(Exception):
    def __init__(self, message):
        self.message = message

class UniqueIder():
    def __init__(self):
        self.__id = 0
        self.__mapping = {}
    def get_id(self, key):
        if key in self.__mapping:
            retval = self.__mapping[key]
        else:
            retval = self.__id + 1
            self.__mapping[key] = retval
            self.__id = retval
        return retval
    def items(self):
        return dict(self.__mapping)

def get_conf(crossref):
    parts = crossref.split("/")
    if parts != "conf" and len(parts) < 2:
        raise FormatError("crossref '%s' was unexpected" % crossref)
    return parts[1]

def process_paper(paperinfo, author_dict, conf_dict):
    year = int(paperinfo["year"][0])
    title = paperinfo["title"][0]
    conf = get_conf(paperinfo.get("crossref", [""])[0])
    confname = paperinfo["booktitle"][0]
    authors = paperinfo.get("author", [])

    if year < 1910 or year > 2020:
        print >> sys.stderr, "bad paper data", paperinfo
        return

    c,_ = Conference.objects.get_or_create(short=conf, full=confname)
    y,_ = ConfYear.objects.get_or_create(conf=c,year=year)
    auths = [Author.objects.get_or_create(name=author)[0] for author in authors]

    try:
        p = Paper(conf=y,title=title)
        p.save()
        p.authors.add(*auths)
        p.save()
    except :
        print >> sys.stderr, "ERROR:", paperinfo


@transaction.commit_manually    
def parse(filename):
    authors = UniqueIder()
    conferences = UniqueIder()
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
                process_paper(paperinfo, authors, conferences)
                paperinfo = None
                counter += 1
                if counter % 1000 == 0:
                    print counter
                if counter > 2000: raise RuntimeError
        except FormatError as e:
            sys.stderr.write("Formatting exception: %s on %s\n" % (e.message, repr(paperinfo)))
            
    def char_data(data):
        global paperinfo, curkey

        if curkey != None:
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
        transaction.commit()
    except Exception, e:
        print e
        transaction.commit()
        #transaction.rollback()

    return 

def sortcounts(yearcounts):
    sortedcounts = []
    for year in sorted(yearcounts.iterkeys()):
        counts = yearcounts[year]
        sortedwords = []
        for term, count in sorted(counts.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            sortedwords.append((term, count))
        sortedcounts.append((year, sortedwords))
    return sortedcounts

if __name__ == "__main__":
    print "parsing dblp.xml"
    fname = len(sys.argv) > 1 and sys.argv[1] or 'dblp.xml'
    yearcounts = parse(fname)
    sortedcounts = sortcounts(yearcounts)
    for year, sortedwords in sortedcounts:
        print year
        for word, count in sortedwords[:30]:
            print "\t%s: %d" % (word, count)

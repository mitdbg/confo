import sys, os
from dblogging import load_logger
import time
import re

ROOT = os.path.abspath('%s/../..' % os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = 'confo.settings'
from django.core.management import setup_environ
from confo import settings
setup_environ(settings)

from confo.home.models import *

(confcache, confycache, authcache, papercache, pacache) = load_logger("w")

class FormatError(Exception):
    def __init__(self, message):
        self.message = message



def get_conf(crossref):
    parts = crossref.split("/")
    if parts != "conf" and len(parts) < 2:
        raise FormatError("crossref '%s' was unexpected" % crossref)
    return parts[1]

def process_paper(paperinfo):
    year = int(paperinfo["year"][0])
    title = paperinfo["title"][0]
#    conf = get_conf(paperinfo.get("crossref", [""])[0])
    confname = paperinfo["booktitle"][0]
    authors = paperinfo.get("author", [])

    if year < 1910 or year > 2020:
        raise FormatError("bad paper year")
        return

    c = confcache.get(confname, {'name':confname}, True)
    y = confycache.get(str(c)+str(year), {'cid': c, 'year': year}, True)
    auths = set([authcache.get(author, {'name':author}, True) for author in authors])

    try:
        p = papercache.get("", {'cid':y, 'title': title}, False)
        for auth in auths:
            pa = pacache.get("", {'paper_id':p, 'author_id': auth}, False)
    except:
        raise FormatError("error building paper")

def parse(filename):
    storekeys = ("year", "title", "author", 'booktitle', 'journal')
    namemap = {"year":"year", "title": "title", "author": "author", "booktitle": "booktitle", "journal": "booktitle"}
    start = ("<inproceedings", "<article")
    end = ("</inproceedings>", "</article>")
    storeres = [re.compile("<(%s)>(.*)</%s>" % (key, key)) for key in storekeys]
    

    toparse = open(filename, "r")
    paperinfo = None
    counter = 0
    for line in toparse:
        if paperinfo == None:
            for tag in start: 
                if line.startswith(tag):
                    paperinfo = {}
                    break
        else:
            noend = True
            for tag in end:
                if line.startswith(tag):
                    try:
                        process_paper(paperinfo)
                    except FormatError,  e:
                        sys.stderr.write("Formatting exception: %s on %s\n" % (e.message, repr(paperinfo)))
                        raise
                            
                    paperinfo = None
                    counter += 1
                    if counter % 10000 == 0:
                        print counter, time.time()
                    noend = False
                    break
            if noend:
                for reg in storeres:
                    match = reg.search(line)
                    if match:
                        key = namemap[match.group(1)]
                        vals = paperinfo.get(key, [])
                        vals.append(match.group(2))
                        paperinfo[key] = vals
                        break

if __name__ == "__main__":
    print "parsing dblp.xml"
    fname = len(sys.argv) > 1 and sys.argv[1] or 'dblp.xml'
    parse(fname)


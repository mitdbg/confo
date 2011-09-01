from nltk.corpus import stopwords
import xml.parsers.expat
import sys

paperinfo = None
curkey = None
stop = set(stopwords.words('english'))

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
    authors = paperinfo.get("author", [])
    
#    print year, conf, title
    
def parse(filename):
    authors = UniqueIder()
    conferences = UniqueIder()
    storekeys = set(("year", "title", "author", "crossref"))
    def start_element(name, attrs):
        global paperinfo, curkey
        if name == "inproceedings":
            paperinfo = {}
        elif paperinfo != None and name in storekeys:
            curkey = name
    def end_element(name):
        global paperinfo, curkey
        try:
            if paperinfo != None and name == "inproceedings":
                process_paper(paperinfo, authors, conferences)
                paperinfo = None
        except FormatError as e:
            sys.stderr.write("Formatting exception: %s on %s\n" % (e.message, repr(paperinfo)))
            
    def char_data(data):
        global paperinfo, curkey
        if curkey != None:
            vals = paperinfo.get(curkey, [])
            vals.append(data)
            paperinfo[curkey] = vals
            curkey = None

    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data
    p.ParseFile(open(filename))
    return yearcounts

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
    yearcounts = parse("dblp.xml")
    sortedcounts = sortcounts(yearcounts)
    for year, sortedwords in sortedcounts:
        print year
        for word, count in sortedwords[:30]:
            print "\t%s: %d" % (word, count)

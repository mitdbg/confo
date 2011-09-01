from nltk.corpus import stopwords
import xml.parsers.expat
import sys

paperinfo = None
curkey = None
stop = set(stopwords.words('english'))

def process_paper(yearcounts, paperinfo):
    year = int(paperinfo["year"])
    title = paperinfo["title"]
    
    wordcount = yearcounts.get(year, {})
    words = [word for word in title.lower().split() if word not in stop]
    for word in words:
        word = word.rstrip(",.?:;'\"()[]-_=+&!~`")
        count = wordcount.get(word, 0)
        wordcount[word] = count + 1
    yearcounts[year] = wordcount

def parse(filename, confid):
    yearcounts = {}
    confkey = "conf/" + confid + "/"
    storekeys = set(("year", "title"))
    def start_element(name, attrs):
        global paperinfo, curkey
        if name == "inproceedings" and attrs["key"].startswith(confkey):
            paperinfo = {}
        elif paperinfo != None and name in storekeys:
            curkey = name
    def end_element(name):
        global paperinfo, curkey
        if paperinfo != None and name == "inproceedings":
            process_paper(yearcounts, paperinfo)
            paperinfo = None
    def char_data(data):
        global paperinfo, curkey
        if curkey != None:
            paperinfo[curkey] = data
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
    if len(sys.argv) != 2:
        print "arguments: conferencekey"
        sys.exit(-1)
    yearcounts = parse("dblp.xml", sys.argv[1])
    sortedcounts = sortcounts(yearcounts)
    for year, sortedwords in sortedcounts:
        print year
        for word, count in sortedwords[:30]:
            print "\t%s: %d" % (word, count)

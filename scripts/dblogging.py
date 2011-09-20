import csv
import os

def load_logger(mode):
    confcache = LogOrCache(["name"], "conferences.txt", mode, "conferences")
    confycache = LogOrCache(["cid","year"], "conferenceyears.txt", mode, "years")
    authcache = LogOrCache(["name"], "authors.txt", mode, "authors")
    papercache = LogOrCache(["cid", "title"], "papers.txt", mode, "papers")
    pacache = LogOrCache(["paper_id", "author_id"], "paperauths.txt", mode, "papers_authors")
    return (confcache, confycache, authcache, papercache, pacache)

class LogOrCache():
    def __init__(self, propnames, logfile, mode, tablename):
        self.map = {}
        self.id = 0
        self.props = ["id"]
        self.props.extend(propnames)
        self.logname = logfile
        try:
            self.logfile = open(logfile, mode)
        except Exception, e:
            print e
        self.tablename = tablename
        if mode == "w":
            self.csvfile = csv.writer(self.logfile)
    def get(self, key, properties, actuallycache):
        try:
            retval = self.map[key]
        except:
            self.id += 1
            retval = self.id
            properties["id"] = retval
            self.csvfile.writerow([properties[k] for k in self.props])
            if actuallycache:
                self.map[key] = retval

        return retval
    def logtodb(self, cursor):
        query = "COPY %s (%s) FROM STDIN WITH CSV;" % (self.tablename,
                                                       ", ".join(self.props))
        path = os.path.abspath(self.logname)
        cmd = "cat %s | psql -c \"%s\" confo confo" % (path, query)
        print cmd
        os.system(cmd)

    def execdb(self, query):
        cmd = "psql -c \"%s\" confo confo" % (query)
        print cmd
        os.system(cmd)
    def close(self):
        self.logfile.close()

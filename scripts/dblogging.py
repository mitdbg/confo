import csv
import os

def load_logger(mode):
    confcache = LogOrCache(["name"], "conferences.txt", mode, "conferences", [
            ("conferences_name", "name"),
            ("conferences_name_like", "name text_pattern_ops"),
            ])
    confycache = LogOrCache(["cid","year"], "conferenceyears.txt", mode, "years", [
            ("years_cid", "cid")
            ])
    authcache = LogOrCache(["name"], "authors.txt", mode, "authors", [
            ("authors_name", "name"),
            ("authors_name_like", "name text_pattern_ops"),
            ])
    papercache = LogOrCache(["cid", "title"], "papers.txt", mode, "papers", [
            ("papers_cid", "cid"),
            ])
    pacache = LogOrCache(["paper_id", "author_id"], "paperauths.txt", mode, "papers_authors", [
           ("papers_authors_author_id", "author_id"),
           ("papers_authors_paper_id", "paper_id")
            ])
    return (confcache, confycache, authcache, papercache, pacache)

class LogOrCache():
    def __init__(self, propnames, logfile, mode, tablename, indices):
        self.map = {}
        self.id = 0
        self.props = ["id"]
        self.props.extend(propnames)
        self.logname = logfile
        self.logfile = open(logfile, mode)
        self.tablename = tablename
        self.indices = indices
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
        for idx in self.indices:
            self.execdb("DROP INDEX %s;" % (idx[0]))

        query = "COPY %s (%s) FROM STDIN WITH CSV;" % (self.tablename,
                                                       ", ".join(self.props))
        path = os.path.abspath(self.logname)
        cmd = "cat %s | psql -c \"%s\" confo confo" % (path, query)
        print cmd
        os.system(cmd)

        for idx in self.indices:
            fields = ", ".join(idx[1:])
            self.execdb("CREATE INDEX %s ON %s (%s);" % 
                        (idx[0], self.tablename, fields))

    def execdb(self, query):
        cmd = "psql -c \"%s\" confo confo" % (query)
        print cmd
        os.system(cmd)

import csv
import os

def load_logger(mode):
    confcache = LogOrCache(["name"], "conferences.txt", mode)
    confycache = LogOrCache(["cid","year"], "conferenceyears.txt", mode)
    authcache = LogOrCache(["name"], "authors.txt", mode)
    papercache = LogOrCache(["cid", "title"], "papers.txt", mode)
    pacache = LogOrCache(["paper_id", "author_id"], "paperauths.txt", mode)
    return (confcache, confycache, authcache, papercache, pacache)

class LogOrCache():
    def __init__(self, propnames, logfile, mode):
        self.map = {}
        self.id = 0
        self.props = ["id"]
        self.props.extend(propnames)
        self.logname = logfile
        self.logfile = open(logfile, mode)
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
    def logtodb(self, cursor, table):
        query = "COPY %s (%s) FROM STDIN WITH CSV;" % (table,
                                                       ", ".join(self.props))
        path = os.path.abspath(self.logname)
                                                       
        cmd = "cat %s | psql -c \"%s\" confo confo" % (path, query)
        print cmd
        os.system(cmd)
        return
        
        
        cmd = "COPY %s (%s) FROM '%s' WITH CSV;" % (
                table,
                ", ".join(self.props),
                os.path.abspath(self.logname))
        print cmd
        cursor.execute(cmd)

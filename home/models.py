from django.db import models
from django.db.models.aggregates import *

class Conference(models.Model):
    class Meta:
        db_table = "conferences"
    name = models.TextField(db_index=True)

    def descriptive_words(self, hide=[]):
        """
        returns the words with IDF values 2*stddev below average
        Represents the most common terms that describe the conference
        """
        stats = self.idfs.aggregate(avg=Avg('idf'), std=StdDev('idf'))
        avg, std = stats['avg'], stats['std']
        #filter(idf__lte=(avg - 2*std)).
        idfs = self.idfs.exclude(word__in=hide).order_by("idf")
        return map(lambda idf:idf.word, idfs)

    def top_by_idf(self, hide=[], years=[]):
        """
        returns the words with IDF values 1 stddev above average
        Represents the most common terms that describe the conference
        """
        stats = self.idfs.aggregate(avg=Avg('idf'), std=StdDev('idf'))
        avg, std = stats['avg'], stats['std']
        idfs = self.idfs.exclude(word__in=hide)
        idfs = idfs.filter(conf = self)
        idfs = idfs.filter(idf__lte=(avg + std), idf__gte=(avg-2*std))
        idfs = idfs.order_by("idf")
        return map(lambda idf: idf.word, idfs)

    def top_by_tfidf(self, hide=[], years=[]):
        ts = Tfidf.objects.filter(conf__conf=self)
        ts = ts.values('word')
        ts = ts.exclude(word__in=hide)
        if years:
            ts = ts.filter(conf__year__in=years)
        ts = ts.annotate(sumcount=Sum('count'),sumscore=Sum('tfidf'))
        ts = ts.order_by('-sumscore')
        return map(lambda t: (t['word'], t['sumcount']), ts)

    def first_paper(self, word):
        try:
            return self.firstpapers.get(word=word).paper
        except:
            return None


class ConferenceCounts(models.Model):
    class Meta:
        db_table = "conf_counts"
    conf = models.OneToOneField(Conference, db_column="cid", related_name="counts", db_index=True)
    count = models.IntegerField()
    minyear = models.IntegerField()
    maxyear = models.IntegerField()
    yearcounts = models.TextField() # number of papers per year

class ConfYear(models.Model):
    class Meta:
        db_table = "years"
    conf = models.ForeignKey(Conference, db_column="cid")
    year = models.IntegerField(db_column="year", db_index=True)


    def top_by_tfidf(self, hide=[]):
        ts = self.tfidfs.exclude(word__in=hide).order_by('-tfidf')
        words = [(tfidf.word, tfidf.tfidf) for tfidf in ts]
        words = words
        return words

    def top_by_count(self, hide=[]):
        cs = self.wordcounts.exclude(word__in=hide).order_by('-count')
        return map(lambda c: (c.word, c.count), cs)

    def similar_papers(self):
        return [sp.paper for sp in self.similarpapers.filter(paper__conf__year__lte=self.year).order_by('paper__conf__year')]

class ConfYearWordCountsManager(models.Manager):
    def trend_by_year(self, word, conf=None):
        wcobj = self.filter(word=word)
        if conf:
            wcobj = wcobj.filter(conf__conf=conf)
        wcobj = wcobj.values("conf__year").annotate(sumcount=Sum('count')).order_by('conf__year')
        return [(d['conf__year'], d['sumcount']) for d in wcobj]


class ConfYearWordCounts(models.Model):
    objects = ConfYearWordCountsManager()    
    class Meta:
        db_table = "year_word_counts"

    conf = models.ForeignKey(ConfYear, db_column='yid', related_name='wordcounts',
                                db_index=True, primary_key=True)
    word = models.CharField(max_length=128, db_column='word', db_index=True)
    count = models.IntegerField()

    

class SimilarConferences(models.Model):
    class Meta:
        db_table = "similar_conferences"
    fromconf = models.ForeignKey(Conference, db_column="fromconf", related_name='similar_from_conferences', db_index=True)
    toconf = models.ForeignKey(Conference, db_column="toconf", related_name='similar_to_conferences')
    similarity = models.FloatField()             

class Author(models.Model):
    class Meta:
        db_table = "authors"
    name = models.TextField(db_column="name", db_index=True)
    pubcount = models.IntegerField(default=-1, db_column='pubcount', null=True)

class Paper(models.Model):
    class Meta:
        db_table = "papers"
    conf = models.ForeignKey(ConfYear, db_column="cid")
    authors = models.ManyToManyField(Author, related_name="papers")
    title = models.TextField(db_column="title", db_index=True)
    
class Word(models.Model):
    class Meta:
        db_table = "words"
    paper = models.ForeignKey(Paper, db_column="pid", db_index=True, related_name="words")
    word = models.CharField(max_length=128, db_column="word", db_index=True)

    

class Tfidf(models.Model):
    class Meta:
        db_table = "year_tfidf"
    conf = models.ForeignKey(ConfYear, db_column="yid", related_name="tfidfs",
                             db_index=True)
    word = models.CharField(max_length=128, db_column='word', db_index=True)
    count = models.IntegerField(db_column="count")
    tfidf = models.FloatField(db_column="tfidf")


class Idf(models.Model):
    class Meta:
        db_table = "conf_idf"
    conf = models.ForeignKey(Conference, db_column="cid", related_name="idfs",
                             db_index=True)
    word = models.CharField(max_length=128, db_column='word', db_index=True)
    idf = models.FloatField(db_column="idf")

class YearPaperSimilarity(models.Model):
    class Meta:
        db_table = "year_paper_similarity"
    confyear = models.ForeignKey(ConfYear, db_column='yid', related_name='similarpapers',
                                 db_index=True)
    paper = models.ForeignKey(Paper, db_column='pid', related_name="similarconfyears",
                              db_index=True)
    dist = models.FloatField(db_column="dist")

class FirstPaper(models.Model):
    class Meta:
        db_table = 'first_papers'

    conf = models.ForeignKey(Conference, db_column='cid', related_name='firstpapers',
                             db_index=True)
    paper = models.ForeignKey(Paper, db_column='pid', related_name="firstpapers",
                              db_index=True)
    word = models.CharField(max_length=128, db_column='word', db_index=True)


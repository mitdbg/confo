from django.db import models

class Conference(models.Model):
    class Meta:
        db_table = "conferences"
    name = models.TextField(db_index=True)

class ConferenceCounts(models.Model):
    class Meta:
        db_table = "conf_counts"
    conf = models.OneToOneField(Conference, db_column="cid", related_name="counts", db_index=True)
    count = models.IntegerField()
    minyear = models.IntegerField()
    maxyear = models.IntegerField()
    yearcounts = models.TextField()

class ConfYear(models.Model):
    class Meta:
        db_table = "years"
    conf = models.ForeignKey(Conference, db_column="cid")
    year = models.IntegerField(db_column="year", db_index=True)

class ConfYearWordCounts(models.Model):
    class Meta:
        db_table = "year_word_counts"
    conf = models.OneToOneField(ConfYear, db_column='yid', related_name='wordcounts',
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
    paper = models.ForeignKey(Paper, db_column="pid", db_index=True)
    word = models.CharField(max_length=128, db_column="word", db_index=True)
    

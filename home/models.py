from django.db import models

class Conference(models.Model):
    class Meta:
        db_table = "conferences"
    name = models.TextField()

class ConferenceCounts(models.Model):
    class Meta:
        db_table = "conf_counts"
    conf = models.OneToOneField(Conference, db_column="cid", related_name="counts")
    count = models.IntegerField()
    minyear = models.IntegerField()
    maxyear = models.IntegerField()
    yearcounts = models.TextField()

class ConfYear(models.Model):
    class Meta:
        db_table = "years"
    conf = models.ForeignKey(Conference, db_column="cid")
    year = models.IntegerField(db_column="year")

class Author(models.Model):
    class Meta:
        db_table = "authors"
    name = models.TextField(db_column="name")
    pubcount = models.IntegerField(default=-1, db_column='pubcount')

class Paper(models.Model):
    class Meta:
        db_table = "papers"
    conf = models.ForeignKey(ConfYear, db_column="cid")
    authors = models.ManyToManyField(Author, related_name="papers")
    title = models.TextField(db_column="title")
    
class Word(models.Model):
    class Meta:
        db_table = "words"
    paper = models.ForeignKey(Paper, db_column="pid")
    word = models.CharField(max_length=128, db_column="word")
    

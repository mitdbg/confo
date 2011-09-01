from django.db import models

class Conference(models.Model):
    short = models.CharField(max_length=30)
    full = models.TextField()

class ConfYear(models.Model):
    conf = models.ForeignKey(Conference)
    year = models.DateField()

class Author(models.Model):
    name = models.TextField()

class Paper(models.Model):
    conf = models.ForeignKey(ConfYear)
    authors = models.ManyToManyField(Author, related_name="papers")
    title = model.TextField()

    

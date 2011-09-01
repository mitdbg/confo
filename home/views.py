# import python libraries
import sys,os

# import django modules
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django import forms
from models import *




def index(request):
    pass

def conference(request, name):
    from django.db import connection, transaction
    cursor = connection.cursor()


    cyears = ConfYear.objects.filter(conf__short__icontains = name)
    years = sorted([cyear.year for cyear in cyears])

    topks = []
    words = set()
    for year in years:
        query = """select word, count(*) as c
        from conferences as c, years as y, papers as p, words as w
        where c.short like '%%s%' and c.id = y.cid and p.cid = c.id and
        w.pid = p.id and y.year = %s
        group by word
        order by c desc
        limit 10"""
        
        cursor.execute(query, [name, year])
        data = cursor.fetchall()
        words.update(map(lambda pair:pair[0], data))
        topks.append((year, data))

    wordtrends = []
    for word in words:
        query = """select year, count(*) as c
        from conferences as c, years as y, papers as p, words as w
        where w.pid = p.id and p.cid = c.id and y.cid = c.id and w.word = %s
        group by year
        order by year asc
        """
        cursor.execute(query, [word])
        d = dict(cursor.fetchall())
        trend = [d.get(year, 0) for year in years]
        wordtrends.append((word, trend))
    cursor.close()
    
    return render_to_response("home/conference.html",
                              {'topks' : topks,
                               'wordtrends' : wordtrends},
                              context_instance=RequestContext(request))

def author(request, name):

    
    
    pass
    

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

from django.db.models import Count


def index(request):
    pass

#def conference_all(request):
#    Conference.objects.

def conference(request, name):
    from django.db import connection, transaction
    cursor = connection.cursor()

    print name
    cyears = ConfYear.objects.filter(conf__name__icontains = name)
    years = sorted(set([cyear.year for cyear in cyears]))
    print "years", years

    topks = []
    words = {}
    for year in years:
        query = """select word, count(*) as c
        from conferences as c, years as y, papers as p, words as w
        where c.id = y.cid and p.cid = y.id and w.pid = p.id and
        c.name ilike %s and y.year = %s 
        group by word
        order by c desc
        limit 10"""
        cursor.execute(query, ['%%%s%%' % name, year])
        data = cursor.fetchall()

        for word, c in data:
            if word not in words: words[word] = c
            words[word] = max(c, words[word])
        
        topks.append((year, data))

    words = sorted(words.items(), key=lambda p:p[1], reverse=True)[:20]

    wordtrends = []
    maxcount = 0
    for word,_ in words:
        query = """select year, count(*) as c
        from conferences as c, years as y, papers as p, words as w
        where w.pid = p.id and p.cid = y.id and y.cid = c.id and
        w.word = %s and c.name like %s        
        group by year
        order by year asc"""
        
        cursor.execute(query, [word, '%%%s%%' % name])
        d = dict(cursor.fetchall())
        trend = [d.get(year, 0) for year in years]
        wordtrends.append((word, trend))
        maxcount = max(maxcount, max(trend))
        print word, maxcount
    wordtrends.sort(key=lambda pair: max(pair[1]), reverse=True)
    cursor.close()

    
    
    return render_to_response("home/conference.html",
                              {'topks' : topks,
                               'wordtrends' : wordtrends,
                               'maxcount' : maxcount},
                              context_instance=RequestContext(request))


def authors_json(request):
    import json    
    term = request.REQUEST.get('term',None)
    if term:
        names = [a.name for a in Author.objects.filter(name__icontains=term).annotate(c=Count('papers')).order_by('-c')[:50]]
    else:
        names = []
    return HttpResponse(json.dumps(names), mimetype='application/json')

def author_all(request):
    auths = Author.objects.annotate(c=Count('papers')).order_by('-c')[:20]
    auths = [[a.name, a.c, a.name.replace(' ','_')] for a in auths]
    return render_to_response("home/author_all.html",
                              {'auths' : auths},
                              context_instance=RequestContext(request))
    

def author(request, name):
    from django.db import connection, transaction
    cursor = connection.cursor()

    name = ' '.join(name.split("_"))

    query = """select c.name, y.year, count(*) as c
    from conferences as c, years as y, papers as p, authors as a, papers_authors as pa
    where a.name like %s and pa.paper_id = p.id and pa.author_id = a.id and
    p.cid = y.id and y.cid = c.id
    group by c.name, y.year
    order by c.name, y.year
    """

    cursor.execute(query, ['%%%s%%' % name])
    confdata = {}
    years = set()
    for row in cursor:
        print row
        confname, year, c = row
        if confname not in confdata: confdata[confname] = {}
        confdata[confname][year] = c
        years.add(year)
    years = range(min(years), max(years) + 1)
    
    ret = []
    maxcount = 0
    for confname, vals in confdata.items():
        counts = [vals.get(year,0) for year in years]
        ret.append((confname, counts))
        maxcount = max(maxcount, max(counts))
                                           
    return render_to_response("home/author.html",
                              {'counts' : ret,
                               'maxcount' : maxcount},
                              context_instance=RequestContext(request))

    

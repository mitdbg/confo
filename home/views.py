# import python libraries
import sys,os,math

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
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from django import forms
from models import *

from django.db.models import Count, Min, Max


def index(request):
    pass

def conference_all(request):
    cs = Conference.objects.all().order_by('-counts__count')
    paginator = Paginator(cs, 25) 

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        cs = paginator.page(page)
    except:
        cs = paginator.page(paginator.num_pages)


    maxcount = max([max(map(int,conf.counts.yearcounts.split(','))) for conf in cs.object_list])
    ret = ConfYear.objects.aggregate(Min('year'), Max('year'))
    nconfs, minyear, maxyear = Conference.objects.all().count(), ret['year__min'],ret['year__max']

    return render_to_response("home/conference_all.html",
                              {'confs' : cs,
                               'minyear' : minyear,
                               'maxyear' : maxyear,
                               'nconfs' : nconfs,
                               'maxcount' : maxcount},
                              context_instance=RequestContext(request))


def conference(request, name):
    from django.db import connection, transaction
    cursor = connection.cursor()

    cyears = ConfYear.objects.filter(conf__name__icontains = name)
    years = sorted(set([cyear.year for cyear in cyears]))

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



    confs = Conference.objects.filter(name__icontains=name)

    ret = ConfYear.objects.aggregate(Min('year'), Max('year'))
    allminyear, allmaxyear = ret['year__min'], ret['year__max']
    allyears = range(allminyear, allmaxyear+1)
    if len(confs):
        conf = confs[0]
        minidx, maxidx = allyears.index(conf.counts.minyear), allyears.index(conf.counts.maxyear)
        print minidx, maxidx, 
        conf.counts.yearcounts = ','.join(conf.counts.yearcounts.split(',')[minidx:maxidx+1])
    
    return render_to_response("home/conference.html",
                              {'topks' : topks,
                               'conf' : conf,
                               'wordtrends' : wordtrends,
                               'maxcount' : maxcount},
                              context_instance=RequestContext(request))


def authors_json(request):
    import json    
    term = request.REQUEST.get('term',None)
    if term:
        auths = Author.objects.filter(name__icontains=term).order_by('-pubcount')[:20]
    else:
        auths = []
    names = [auth.name for auth in auths]
    return HttpResponse(json.dumps(names), mimetype='application/json')

def author_all(request):
    auths = Author.objects.filter(pubcount__gt=0).order_by('-pubcount')

    paginator = Paginator(auths, 25) 

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        auths = paginator.page(page)
    except:
        auths = paginator.page(paginator.num_pages)

    print auths.object_list
    return render_to_response("home/author_all.html",
                              {'auths' : auths},
                              context_instance=RequestContext(request))
    

def author(request, name):
    from django.db import connection, transaction
    cursor = connection.cursor()

    #name = ' '.join(name.split("_"))

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

    ret.sort(key=lambda (cname,counts): max(counts), reverse=True)




    # terms information
    
    # terms information
    query = """select word, count(*) as c
    from words as w, authors as a, papers as p, papers_authors as ap
    where ap.paper_id = p.id and ap.author_id = a.id and
    a.name ilike %s and w.pid = p.id
    group by w.word
    order by c desc
    limit 20
    """
    cursor.execute(query, ['%%%s%%' % name])
    allwords = [(w,c) for w,c in cursor]
    wordyears = {}
    if len(allwords):
        maxwordcount = max(allwords, key=lambda p: p[1])[1]
        allwords = map(lambda (w,c): (w,c, int(math.ceil(25.0 * c / maxwordcount)) + 5), allwords)

        query = """select y.year, word, count(*) as c
        from words as w, authors as a, papers as p, papers_authors as ap, years as y
        where ap.paper_id = p.id and ap.author_id = a.id and p.cid = y.id and
        a.name ilike %s and w.pid = p.id
        group by w.word, y.year
        order by y.year asc, c desc
        """
        cursor.execute(query, ['%%%s%%' % name])
        words = []
        for y, word, c in cursor:
            words = wordyears.get(y, [])
            if len(words) > 20: continue
            words.append((word, c))
            wordyears[y] = words

        for y in wordyears.keys():
            words = wordyears[y]
            words = map(lambda (w,c): (w,c, int(math.ceil(25 * float(c) / maxwordcount)) + 5), words)
            wordyears[y] = words

        
    
                                           
    return render_to_response("home/author.html",
                              {'counts' : ret,
                               'maxcount' : maxcount,
                               'name' : name,
                               'wordyears' : wordyears,
                               'allwords' : allwords},
                              context_instance=RequestContext(request))

    

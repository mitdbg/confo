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
from django.views.decorators.cache import cache_page


from django import forms
from models import *

from django.db.models import Count, Min, Max

def test(request):
    return render_to_response("home/test.html", {}, context_instance=RequestContext(request))

@cache_page(60 * 1000)
def index(request):
    return render_to_response("home/index.html", {}, context_instance=RequestContext(request))

@cache_page(60 * 1000)
def conference_all(request, cs=None):
    if cs == None:
        cs = Conference.objects.all()
    cs = cs.order_by('-counts__count')
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

    if len(cs.object_list):
        maxcount = max([max(map(int,conf.counts.yearcounts.split(','))) for conf in cs.object_list])
        ret = ConfYear.objects.filter(conf__in=cs.object_list).aggregate(Min('year'), Max('year'))
        nconfs, minyear, maxyear = cs.object_list.count(), ret['year__min'],ret['year__max']
    else:
        maxcount = 0
        ret = []
        nconfs, minyear, maxyear = 0,0,0

    return render_to_response("home/conference_all.html",
                              {'confs' : cs,
                               'minyear' : minyear,
                               'maxyear' : maxyear,
                               'nconfs' : nconfs,
                               'maxcount' : maxcount},
                              context_instance=RequestContext(request))

@cache_page(60 * 1000)
def conference(request, name):
    # check if name is unique?
    try:
        Conference.objects.get(name=name)
    except:
        cs = Conference.objects.filter(name__icontains = name)
        if len(cs) != 1:
            return conference_all(request, cs)


    
    from django.db import connection, transaction
    cursor = connection.cursor()

    cyears = ConfYear.objects.filter(conf__name = name)
    years = sorted(set([cyear.year for cyear in cyears]))
    years = range(min(years), max(years) + 1)

    topks = []
    overall = []
    words = {}
    for year in years:
        query = """select word, count(*) as c
        from conferences as c, years as y, papers as p, words as w
        where c.id = y.cid and p.cid = y.id and w.pid = p.id and
        c.name = %s and y.year = %s 
        group by word
        order by c desc
        limit 10"""
        cursor.execute(query, [name, year])
        data = cursor.fetchall()

        for word, c in data:
            if word not in words: words[word] = c
            words[word] = max(c, words[word])
        if len(data):
            topks.append((year, data))
        overall.append(sum([p[1] for p in data]))

    words = sorted(words.items(), key=lambda p:p[1], reverse=True)[:20]

    wordtrends = []
    maxcount = 0
    for word,_ in words:
        query = """select year, count(*) as c
        from conferences as c, years as y, papers as p, words as w
        where w.pid = p.id and p.cid = y.id and y.cid = c.id and
        w.word = %s and c.name = %s
        group by year
        order by year asc"""
        
        cursor.execute(query, [word, name])
        d = dict(cursor.fetchall())
        trend = [d.get(year, 0) for year in years]
        wordtrends.append((word, trend))
        maxcount = max(maxcount, max(trend))
        print word, maxcount
    wordtrends.sort(key=lambda pair: max(pair[1]), reverse=True)
    cursor.close()


    
    conf = Conference.objects.get(name=name)
    
    return render_to_response("home/conference.html",
                              {'topks' : topks,
                               'conf' : conf,
                               'overall' : overall,
                               'wordtrends' : wordtrends,
                               'maxcount' : maxcount},
                              context_instance=RequestContext(request))


def conferences_json(request):
    import json    
    term = request.REQUEST.get('term',None)
    if term:
        confs = Conference.objects.filter(name__icontains=term).order_by('-counts__count')[:20]
    else:
        confs = []
    names = []
    for c in confs:
        if len(c.name) > 20:
            names.append('%s...' % c.name[:20])
        else:
            names.append(c.name)
    return HttpResponse(json.dumps(names), mimetype='application/json')


def authors_json(request):
    import json    
    term = request.REQUEST.get('term',None)
    if term:
        auths = Author.objects.filter(name__icontains=term).order_by('-pubcount')[:20]
    else:
        auths = []
    names = [auth.name for auth in auths]
    return HttpResponse(json.dumps(names), mimetype='application/json')


@cache_page(60 * 100)
def author_all(request, auths=None):
    if auths == None:
        auths = Author.objects.all()
    auths = auths.filter(pubcount__gt=0).order_by('-pubcount')

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

    return render_to_response("home/author_all.html",
                              {'auths' : auths},
                              context_instance=RequestContext(request))
    
@cache_page(60 * 100)
def author(request, name=None):
    # check if name is unique?
    try:
        author = Author.objects.get(name=name)
    except:
        print "blah"
        if not name: name = request.REQUEST.get('name', None)
        if not name:
            return author_all(request)
        auths = Author.objects.filter(name__icontains = name)
        if len(auths) > 1:
            return author_all(request, cs)
        return author_all(request)


    
    from django.db import connection, transaction
    cursor = connection.cursor()


    query = """select c.name, y.year, count(*) as c
    from conferences as c, years as y, papers as p, authors as a, papers_authors as pa
    where a.name ilike %s and pa.paper_id = p.id and pa.author_id = a.id and
    p.cid = y.id and y.cid = c.id
    group by c.name, y.year
    order by c.name, y.year
    """

    cursor.execute(query, ['%%%s%%' % name])
    confdata = {}
    overallcounts = {}
    years = set()

    for row in cursor:
        print row
        confname, year, c = row
        if confname not in confdata: confdata[confname] = {}
        confdata[confname][year] = c
        years.add(year)
        overallcounts[year] = overallcounts.get(year,0) + c
    years = range(min(years), max(years) + 1)
    
    ret = []
    maxcount = 0
    for confname, vals in confdata.items():
        counts = [vals.get(year,0) for year in years]
        ret.append((confname, counts))
        maxcount = max(maxcount, max(counts))
    overallcounts = [overallcounts.get(year,0) for year in years]

    ret.sort(key=lambda (cname,counts): max(counts), reverse=True)



    
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
        uniquewords = {}
        for y, word, c in cursor:
            words = wordyears.get(y, [])
            if len(words) > 20: continue
            words.append((word, c))
            wordyears[y] = words
            uniquewords[word] = uniquewords.get(word,0)+c

        for y in wordyears.keys():
            words = wordyears[y]            
            words = map(lambda (w,c): (w,(c, int(math.ceil(25 * float(c) / maxwordcount)) + 5)), words)
            words = dict(words)
            wordyears[y] = words

        uniquewords = [p[0] for p in sorted(uniquewords.items(), key=lambda p: p[1], reverse=True)[:10]]
        years = range(min(wordyears.keys()), max(wordyears.keys())+1)
        labels = []
        labels.extend(map(str,years))
        labels.append('name')
        table = []


        labels = dict([(label, {"name" : label, 'unit': ''}) for label in labels])

        
        for word in uniquewords:
            row = {'name' : word}
            prev = 0
            for year in years:
                cur = wordyears.get(year,{}).get(word, (0,0))[0]
                row[str(year)] = cur
                prev = cur
            table.append(row)
        import json
        labels = json.dumps(labels)            
        table = json.dumps(table)
    
                                           
    return render_to_response("home/author.html",
                              {'counts' : ret,
                               'overallcounts': overallcounts,
                               'maxcount' : maxcount,
                               'author' : author,
                               'wordyears' : {},#wordyears,
                               'allwords' : allwords,
                               'pcdata' : table,
                               'pclabels' : labels},
                              context_instance=RequestContext(request))

    

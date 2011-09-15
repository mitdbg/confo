# import python libraries
import sys,os,math,json

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
from django.db import connection, transaction


from django import forms
from models import *

from django.db.models import Count, Min, Max

def test(request):
    return render_to_response("home/test.html", {}, context_instance=RequestContext(request))


#@cache_page(60 * 1000)
def index(request):
    return render_to_response("home/index.html",
                              {},
                              context_instance=RequestContext(request))



#@cache_page(60 * 1000)
def conference_all(request, cs=None):
    if cs == None:
        cs = Conference.objects.all()
    cs = cs.order_by('-counts__count')
    nconfs = cs.count()
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
        minyear, maxyear = ret['year__min'],ret['year__max']
    else:
        maxcount = 0
        ret = []
        minyear, maxyear = 0,0

    return render_to_response("home/conference_all.html",
                              {'confs' : cs,
                               'minyear' : minyear,
                               'maxyear' : maxyear,
                               'nconfs' : nconfs,
                               'maxcount' : maxcount},
                              context_instance=RequestContext(request))

#@cache_page(60 * 1000)
def conferencenoyears(request, name):
    return conference(request,name,-1,-1)

def conference(request, name, startyear, endyear):
    # check if name is unique?
    startyear=int(startyear)
    endyear=int(endyear)
    print "startyear=",startyear,"endyear=",endyear
    
    try:
        conf = Conference.objects.get(name=name)
    except:
        cs = Conference.objects.filter(name__icontains = name)
        if len(cs) != 1:
            return conference_all(request, cs)
        conf = cs[0]

        
    hidelist=[]
    hidestr = request.GET.get('hidden', '')
    if hidestr.strip():
        hidelist= [str(w.strip()) for w in hidestr.split(',') if len(w.strip()) > 0]
            

    cyears = conf.confyear_set.order_by('year')
    years = [cyear.year for cyear in cyears]
    minyear, maxyear = min(years), max(years)
    if (startyear != -1 and startyear >= minyear):
        curstartyear = startyear
    else:
        curstartyear = minyear

    if (endyear != -1 and endyear <= maxyear):
        curendyear = endyear
    else:
        curendyear = maxyear

    years = range(curstartyear, curendyear + 1)

    # topks = []
    # for cyear in cyears:
    #     data = cyear.top_by_tfidf(hide=hidelist)[:10]
    #     if len(data):
    #         topks.append((cyear.year, data))

    # # add term data aggregated over all years
    # data = conf.top_by_tfidf(years=years)[:10]
    # if len(data):
    #     topks.append(("all", data))
        

    #words = conf.top_by_tfidf(hide=hidelist, years=years)[:30]
    #words = map(lambda x:x[0], words)
    words = conf.descriptive_words(hide=hidelist)[:20]

    # get sparkline counts per word
    wordtrends = []
    maxcount = 0
    for word in words:
        d = dict(ConfYearWordCounts.objects.trend_by_year(word, conf))
        trend = [d.get(year, 0) for year in years]
        paper = conf.first_paper(word)
        wordtrends.append((word, trend, paper))
        maxcount = max(maxcount, max(trend))
    wordtrends.sort(key=lambda pair: max(pair[1]), reverse=True)

    # list of top words (by tfidf) and papers by year
    cyarr = cyears.filter(year__in=years)
    years = [cy.year for cy in cyarr]
    tfidf_by_year = [cy.top_by_tfidf()[:10] for cy in cyarr]
    count_by_year = [cy.top_by_count()[:10] for cy in cyarr]
    papers_by_year = [cy.similar_papers()[:10] for cy in cyarr]

    stats_by_year = zip(years, tfidf_by_year, count_by_year, papers_by_year)
    

    sim_conf = SimilarConferences.objects.filter(fromconf = conf).order_by('-similarity')

    return render_to_response("home/conference.html",
                              {'conf' : conf,
                               'wordtrends' : wordtrends,
                               'maxcount' : maxcount,
                               'hidden': hidelist,
                               'years': range(minyear,maxyear+1),
                               'selectedstartyear': curstartyear,
                               'selectedendyear': curendyear,
                               'stats_by_year' : stats_by_year,
                               'similarconferences': sim_conf,
                               },
                              context_instance=RequestContext(request))


def conferences_json(request):
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
    nauth = auths.count()
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
                              {'auths' : auths,
                               'nauth' : nauth
                               },
                              context_instance=RequestContext(request))
    
@cache_page(60 * 100)
def author(request, name=None):
    # check if name is unique?
    try:
        author = Author.objects.get(name=name)
    except:
        if not name: name = request.REQUEST.get('name', None)
        if not name:
            return author_all(request)
        auths = Author.objects.filter(name__icontains = name)
        if len(auths) > 1:
            return author_all(request, auths)
        elif len(auths) == 0:
            return author_all(request)
        author = auths[0]


    cursor = connection.cursor()

    # calculate # publications per year for each conference
    query = """select c.name, y.year, count(*) as c
    from conferences as c, years as y, papers as p, authors as a, papers_authors as pa
    where a.id = %s and pa.paper_id = p.id and pa.author_id = a.id and
    p.cid = y.id and y.cid = c.id
    group by c.name, y.year
    order by c.name, y.year
    """

    cursor.execute(query, [author.pk])
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

    ret.sort(key=lambda (cname,counts): sum(counts), reverse=True)



    
    # terms information
    query = """select word, count(*) as c
    from words as w, authors as a, papers as p, papers_authors as ap
    where ap.paper_id = p.id and ap.author_id = a.id and
    a.id = %s and w.pid = p.id
    group by w.word
    order by c desc
    limit 20
    """
    cursor.execute(query, [author.pk])
    allwords = [(w,c) for w,c in cursor]
    wordyears = {}
    if len(allwords):
        maxwordcount = max(allwords, key=lambda p: p[1])[1]
        allwords = map(lambda (w,c): (w,c, int(math.ceil(25.0 * c / maxwordcount)) + 5), allwords)

        query = """select y.year, word, count(*) as c
        from words as w, authors as a, papers as p, papers_authors as ap, years as y
        where ap.paper_id = p.id and ap.author_id = a.id and p.cid = y.id and
        a.id = %s and w.pid = p.id
        group by w.word, y.year
        order by y.year asc, c desc
        """
        cursor.execute(query, [author.pk])
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
    else:
        table = json.dumps([])
        labels = json.dumps([])
    
                                           
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

    

@cache_page(60 * 100)
def firstname_hist(request, fname):
    q = """select ((pubcount/5.0)::int)*5 as intpubcount, count(*) as nauthors 
    from authors where split_part(name, ' ', 1) ilike %s 
    group by intpubcount order by intpubcount;"""

    cursor = connection.cursor()
    cursor.execute(q, ['%%%s%%' % fname])
    d = dict(cursor.fetchall())

    pubcounts = [(x, d.get(x, 0)) for x in range(0, 465, 5)]
    return HttpResponse(json.dumps(pubcounts), mimetype='application/json')
    
    
    
@cache_page(60 * 1000)
def fname(request):

    cursor = connection.cursor()

    fnamecounts = {}
    bucksize = 5
    q = """select afn.fname,  ((afn.pubcount/%d.0)::int-1)*%d as intpubcount, count(*) as nauthors 
    from authors_by_fname as afn,
      (select fname as topfname
       from fname_overall_stats
       where char_length(fname) > 2
       order by count * avg desc limit 10) as tops
    where tops.topfname = afn.fname
    group by afn.fname, intpubcount
    order by afn.fname, intpubcount;""" % (bucksize,bucksize)

    cursor.execute(q)
    res = {}
    for fname, pubcount, nauthors in cursor:
        d = res.get(fname, {})
        d[pubcount] = nauthors
        res[fname] = d
        
    for fname, d in res.items():
        pubcounts = [d.get(x, 0) for x in range(0, 200, bucksize)]
        total = sum(pubcounts)
        total = 1
        pubcounts = [sum(pubcounts[i:])/float(total) for i in xrange(len(pubcounts))]
        fnamecounts[fname] = pubcounts
        print fname, pubcounts

    labels = ['Count']
    labels.extend(fnamecounts.keys())
    table = []
    for idx,x in enumerate(range(0, 200, bucksize)):
        row = ["'%d'" % (x)]
        for counts in fnamecounts.values():
            row.append(str(counts[idx]))
        table.append('[%s]' % ','.join(row))
    

    return render_to_response("home/firstname.html",
                              {'fnamecounts' : fnamecounts,
                               'labels' : labels,
                               'table' : table
                               },
                              context_instance=RequestContext(request))

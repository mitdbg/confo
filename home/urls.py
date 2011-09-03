from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('home.views',
                       (r'^$', 'index'),
                       (r'^conference/$', 'conference_all'),
                       (r'^conference/(\w.*)/$', 'conference'),                       
                       (r'^author/$', 'author_all'),
                       (r'^author/(\w.*)/$', 'author'),
                       (r'^authors/json/$', 'authors_json'),
                       )


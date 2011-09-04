from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('home.views',
                       (r'^$', 'index'),
                       (r'^conference/$', 'conference_all'),
                       (r'^conference/(\w.*)/$', 'conference'),

                       (r'^author/$', 'author'),
                       (r'^author/(\w.*)/$', 'author'),

                       (r'^conferences/json/$', 'conferences_json'),
                       (r'^authors/json/$', 'authors_json'),
                       (r'^test/$', 'test'),

                       (r'^stats/fname/hist/(\w+)/$', 'firstname_hist'),
                       )


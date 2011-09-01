from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('home.views',
                       (r'^$', 'index'),
                       (r'^conf/(\w+)/$', 'conference'),
                       (r'^auth/([\w \d]+)/$', 'author')
                       )


#! /usr/bin/env python2.7
import sys
import os
import django.core.handlers.wsgi
sys.path.append('/data/confo/')
sys.path.append('/data/confo/confo/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'confo.settings'
application = django.core.handlers.wsgi.WSGIHandler()


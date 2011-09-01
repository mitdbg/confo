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
    
    

    
    return render_to_response("home/conference.html", {},
                              context_instance=RequestContext(request))

def author(request, name):

    
    
    pass
    

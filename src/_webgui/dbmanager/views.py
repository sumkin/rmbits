import os
import ConfigParser
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from split_history_upload_form import *

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

def index(request):

    if request.method == 'POST':

        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            return HttpResponseRedirect('/success')

    else:
        form = UploadFileForm()

    c = {'form': form}
    c.update(csrf(request))

    return render_to_response('dbmanager_index.htm', {'form': form})

def split_history_upload(request):

    return HttpResponse('Yes!')





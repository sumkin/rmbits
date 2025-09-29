from django.shortcuts import render_to_response
from django.template import Context, RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect

from models import SigODList
from forms import SigODListForm

def index(request):
  print request.GET
  print request.POST
  if request.method == 'POST':
    form = SigODListForm(request.POST,request.FILES)
    if form.is_valid():
      # Workaround when no file were uploaded
      try:
        fname = request.FILES['fname']
      except:
        fname = ''
      upload = SigODList(email = request.POST['email'],
                         old_dfrom = request.POST['old_dfrom'],
                         old_dto = request.POST['old_dto'],
                         new_dfrom = request.POST['new_dfrom'],
                         new_dto = request.POST['new_dto'],
                         fname = fname)
      upload.save()

      # Redirect to thankyou page
      return HttpResponseRedirect('/sigod/thankyou')
  else:
    form = SigODListForm()

  tmpl = loader.get_template('sigod/index.htm')
  cntx = RequestContext(request,{'form':form})
  return HttpResponse(tmpl.render(cntx))

def thankyou(request):
  tmpl = loader.get_template('sigod/thankyou.htm')
  cntx = Context({})
  return HttpResponse(tmpl.render(cntx))



from django.shortcuts import render_to_response
from django.template import Context, RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect

from models import RADataUpload
from forms import RADataUploadForm

def new(request):
  if request.method == 'POST':
    form = RADataUploadForm(request.POST,request.FILES) 
    if form.is_valid():
      upload = RADataUpload(email=request.POST['email'],fname=request.FILES['fname'])

      upload.save()

      # Redirect to the thank you page.
      return HttpResponseRedirect('/radata/thankyou/')
  else:
    form = RADataUploadForm()

  tmpl = loader.get_template('radata/form.html')
  cntx = RequestContext(request,{'form':form})
  return HttpResponse(tmpl.render(cntx))

def thankyou(request):
  tmpl = loader.get_template('radata/thankyou.html')
  cntx = Context({})
  return HttpResponse(tmpl.render(cntx))



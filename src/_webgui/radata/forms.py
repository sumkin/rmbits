from datetime import datetime
from django.db import models
from django import forms

from models import RADataUpload

class RADataUploadForm(forms.ModelForm):
  class Meta:
    model = RADataUpload

  def is_valid(self):
    return True

  def save(self,commit=True,fail_silent=True):
    super(RADataUploadForm,self).save(commit) 

 

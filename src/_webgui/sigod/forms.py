from datetime import datetime
from django.db import models
from django import forms

from models import SigODList

class SigODListForm(forms.ModelForm):
  class Meta:
    model = SigODList
    fields = {'email','old_dfrom','old_dto','new_dfrom','new_dto','fname'}

  def is_valid(self):
    return True

  def save(self,commit=True,fail_silent=True):
    print self
    super(SigODListForm,self).save(commit)



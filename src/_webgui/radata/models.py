import csv
from datetime import datetime, date, timedelta
import sqlite3
from multiprocessing import Process

from django.db import models
from django.conf import settings

from neo4j_updater import *
from or_data_updater import *

def update_neo4j(fname):
  nu = Neo4jUpdater(fname)
  nu.update()

def update_or_data(fname):
  odu = OrDataUpdater(fname)
  odu.update()

def update_dbs(fname):
  update_neo4j(fname)
  update_or_data(fname)

def callback():
  pass    

class RADataUpload(models.Model):
  email = models.EmailField()
  fname = models.FileField(upload_to='ra.data')
  dt_upload = models.DateField()

  def save(self):
    if not self.dt_upload:
      self.dt_upload = datetime.today()
    super(RADataUpload,self).save()

    fname = settings.MEDIA_ROOT + self.fname.name

    p = Process(target=update_dbs,args=[fname])
    p.start()



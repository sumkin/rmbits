import os
import sys
import csv
from datetime import datetime,date,timedelta
from multiprocessing import Process
import ConfigParser

from django.db import models
from django.conf import settings

from emailsender.email_sender import EmailSender

import ConfigParser

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
sys.path.append(config.get('PATHS','datamanager'))

import sigodlib
import csvlib

def create_sigod_list(email,old_dfrom,old_dto,new_dfrom,new_dto,fname=''):
  old_dfroms = old_dfrom.split('-')
  old_dtos = old_dto.split('-')
  new_dfroms = new_dfrom.split('-')
  new_dtos = new_dto.split('-')

  old_dfrom = date(int(old_dfroms[0]),int(old_dfroms[1]),int(old_dfroms[2]))
  old_dto = date(int(old_dtos[0]),int(old_dtos[1]),int(old_dtos[2]))
  new_dfrom = date(int(new_dfroms[0]),int(new_dfroms[1]),int(new_dfroms[2]))
  new_dto = date(int(new_dtos[0]),int(new_dtos[1]),int(new_dtos[2]))

  print 'Creating lists...'
  old_sl_rev = sigodlib.sigod_list_rev(old_dfrom,old_dto,limit=3000)
  new_sl_rev = sigodlib.sigod_list_rev(new_dfrom,new_dto,limit=3000)
  old_sl_npax = sigodlib.sigod_list_npax(old_dfrom,old_dto,limit=3000)
  new_sl_npax = sigodlib.sigod_list_npax(new_dfrom,new_dto,limit=3000)
  added_sl,removed_sl = sigodlib.sigod_lists_diff(old_sl_rev,new_sl_rev)

  print 'Creating files from the list...'
  sigod_data = config.get('PATHS','sigod_data')
  old_fname_rev = csvlib.create_file_from_list('old_top_ods_rev.csv',sigod_data,old_sl_rev)
  new_fname_rev = csvlib.create_file_from_list('new_top_ods_rev.csv',sigod_data,new_sl_rev)
  old_fname_npax = csvlib.create_file_from_list('old_top_ods_npax.csv',sigod_data,old_sl_npax)
  new_fname_npax = csvlib.create_file_from_list('new_top_ods_npax.csv',sigod_data,new_sl_npax)  

  # Revenue figures
  rev_in_old_sl = old_sl_rev[len(old_sl_rev)-1][6]
  npax_in_old_sl = old_sl_npax[len(old_sl_npax)-1][6]
  rev_in_new_sl = new_sl_rev[len(new_sl_rev)-1][6]
  npax_in_new_sl = new_sl_npax[len(new_sl_npax)-1][6] 

  print 'Calculating total revenue...'
  tot_rev_old = sigodlib.total_rev(old_dfrom,old_dto)
  tot_rev_new = sigodlib.total_rev(new_dfrom,new_dto)
  tot_npax_old = sigodlib.total_npax(old_dfrom,old_dto)
  tot_npax_new = sigodlib.total_npax(new_dfrom,new_dto)

  # Calculate revenue in provided SigOD list
  if fname != '':
    print 'Calculating share in current SigOD list...'
    rev_in_file_old = sigodlib.rev_in_file(old_dfrom,old_dto,fname)
    rev_in_file_new = sigodlib.rev_in_file(new_dfrom,new_dto,fname)
    npax_in_file_old = sigodlib.npax_in_file(old_dfrom,old_dto,fname)
    npax_in_file_new = sigodlib.npax_in_file(new_dfrom,new_dto,fname)

  added_fname = csvlib.create_file_from_list('added_top_ods_rev.csv',sigod_data,added_sl)
  removed_fname = csvlib.create_file_from_list('removed_top_ods_rev.csv',sigod_data,removed_sl)

  print 'Sending email...'
  # Send email
  es = EmailSender('157.200.13.44',25)
  sbj = 'SigOD list update'
  txt  = 'Hello,'
  txt += '\n\n'
  if fname != '':
    txt += 'Revenue in current SigOD list (old): '+str(int(rev_in_file_old))+' / '+str(int(tot_rev_old))+' = '+str(int(100*(float(rev_in_file_old)/float(tot_rev_old))))+'%\n'
    txt += 'Revenue in current SigOD list (new): '+str(int(rev_in_file_new))+' / '+str(int(tot_rev_new))+' = '+str(int(100*(float(rev_in_file_new)/float(tot_rev_new))))+'%\n'
    txt += 'Number pax in current SigOD list (old): '+str(int(npax_in_file_old))+' / '+str(int(tot_npax_old))+' = '+str(int(100*(float(npax_in_file_old)/float(tot_npax_old))))+'%\n'
    txt += 'Number pax in current SigOD list (new): '+str(int(npax_in_file_new))+' / '+str(int(tot_npax_new))+' = '+str(int(100*(float(npax_in_file_new)/float(tot_npax_new))))+'%\n'
    txt += '\n' 
  txt += 'Revenue in old list:  '+str(int(rev_in_old_sl))+' / '+str(int(tot_rev_old))+' = '+str(int(100*float(rev_in_old_sl)/float(tot_rev_old)))+'%\n'
  txt += 'Revenue in new list:  '+str(int(rev_in_new_sl))+' / '+str(int(tot_rev_new))+' = '+str(int(100*float(rev_in_new_sl)/float(tot_rev_new)))+'%\n'
  txt += 'Number of pax in old list:  '+str(int(npax_in_old_sl))+' / '+str(int(tot_npax_old))+' = '+str(int(100*float(npax_in_old_sl)/float(tot_npax_old)))+'%\n'
  txt += 'Number of pax in new list:  '+str(int(npax_in_new_sl))+' / '+str(int(tot_npax_new))+' = '+str(int(100*float(npax_in_new_sl)/float(tot_npax_new)))+'%\n'
  txt += '\n'
  txt += 'Old date range: '+old_dfrom.strftime('%Y-%m-%d')+' --- '+old_dto.strftime('%Y-%m-%d')+'\n'
  txt += 'New date range: '+new_dfrom.strftime('%Y-%m-%d')+' --- '+new_dto.strftime('%Y-%m-%d')+'\n'
  txt += '\n'
  txt += 'Files for SigOD list update are attached.'
  txt += '\n\n'
  txt += '\"old_top_ods_rev.csv\"\n'
  txt += '-----------------------\n'
  txt += 'TopODs by revenue for period '+old_dfrom.strftime('%d.%m.%Y')+'-'+old_dto.strftime('%d.%m.%Y')
  txt += '\n\n'
  txt += '\"new_top_ods_rev.csv\"\n'
  txt += '-----------------------\n'
  txt += 'TopODs by revenue for period '+new_dfrom.strftime('%d.%m.%Y')+'-'+new_dto.strftime('%d.%m.%Y')
  txt += '\n\n'
  txt += '\"old_top_ods_npax.csv\"\n'
  txt += '-----------------------\n'
  txt += 'TopODs by number of pax for period '+old_dfrom.strftime('%d.%m.%Y')+'-'+old_dto.strftime('%d.%m.%Y')
  txt += '\n\n'
  txt += '\"new_top_ods_npax.csv\"\n'
  txt += '--------------------------\n'
  txt += 'TopODs by number of pax for period '+new_dfrom.strftime('%d.%m.%Y')+'-'+new_dto.strftime('%d.%m.%Y')
  txt += '\n\n'
  txt += '\"added_top_ods.csv\"\n'
  txt += '-----------------------\n'
  txt += 'TopODs by revenue presented in new list, but missing in old one.'
  txt += '\n\n'
  txt += '\"removed_top_ods.csv\"\n'
  txt += '------------------------\n'
  txt += 'TopODs by revenue presented in old list, but missing in new one.'
  txt += '\n\n'
  txt += 'Regards,\nFedor'

  attached = [old_fname_rev,new_fname_rev,old_fname_npax,new_fname_npax,added_fname,removed_fname]

  es.send_multipart(email,'fedor.nikitin@finnair.com',sbj,txt,attached)
  es.send_multipart('fedor.nikitin@finnair.com',email,sbj,txt,attached)

class SigODList(models.Model):
  email = models.EmailField()
  old_dfrom = models.DateField()
  old_dto = models.DateField()
  new_dfrom = models.DateField()
  new_dto = models.DateField()
  fname = models.FileField(upload_to='sigod.data',null=True)
  dt_upload = models.DateField()

  def save(self):
    if not self.dt_upload:
      self.dt_upload = datetime.today()
    super(SigODList,self).save()

    fname = settings.MEDIA_ROOT + self.fname.name
    old_dfrom = self.old_dfrom
    old_dto = self.old_dto
    new_dfrom = self.new_dfrom
    new_dto = self.new_dto
    email = self.email

    p = Process(target=create_sigod_list,args=[email,old_dfrom,old_dto,new_dfrom,new_dto,fname])
    p.start()




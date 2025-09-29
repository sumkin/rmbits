from django.db import models

class ClassUsage(models.Model):

    OLD_NEW_CHOICES = (('OLD','OLD'),
                       ('NEW','NEW'),)

    fromm     = models.CharField('FROM',max_length=10,help_text='Input airport, city, region, country or continent')
    to        = models.CharField('TO',max_length=10,help_text='Input airport, city, region, country or continent')
    cls       = models.CharField('CLASSES',max_length=26,help_text='Input classes without commas as one string. Example: CDAF')
    old_new   = models.CharField('OLD/NEW',max_length=3,choices=OLD_NEW_CHOICES)
    type_p2p  = models.BooleanField('POINT TO POINT')
    type_lh   = models.BooleanField('LONG-HAUL')
    type_ie   = models.BooleanField('INTRA-EUROPE')
    min_stay  = models.IntegerField('MIN STAY',blank=True,null=True)
    max_stay  = models.IntegerField('MAX STAY',blank=True,null=True)
    ap        = models.IntegerField('AP',blank=True,null=True)
    refund_pr = models.BooleanField('PARTIAL REFUND')
    refund_fr = models.BooleanField('FULL REFUND')
    refund_nr = models.BooleanField('NO REFUND')
    chng_cwof = models.BooleanField('CHANGES WITHOUT FEE')
    chng_cwf  = models.BooleanField('CHANGES WITH FEE')
    chng_nc   = models.BooleanField('NO CHANGES')

    def __unicode__(self):
        return self.fromm + "-" + self.to + "_" + self.cls + "_" + self.old_new 

    


 

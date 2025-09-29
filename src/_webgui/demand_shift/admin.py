from django.contrib import admin
from demand_shift.models import ClassUsage
from demand_shift.actions import export_as_csv

class ClassUsageAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Itinerary', {'fields': ['fromm','to','cls','old_new']}),
        ('Traffic category', {'fields': [('type_p2p','type_lh','type_ie')]}),
        ('Stay', {'fields': [('min_stay','max_stay')]}),
        ('Advanced purchase', {'fields': ['ap']}),
        ('Refund', {'fields': [('refund_fr','refund_pr','refund_nr')]}),
        ('Changes', {'fields': [('chng_cwof','chng_cwf','chng_nc')]}),
    ]
    actions = [export_as_csv]
admin.site.register(ClassUsage,ClassUsageAdmin)

 

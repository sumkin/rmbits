from django.views.static import *
from django.conf import settings
from django.conf.urls.defaults import *
#from autocomplete.views import autocomplete

#
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
#

#import autocomplete_settings

urlpatterns = patterns('',
    # Example:
    # (r'^webgui/', include('webgui.foo.urls')),

    #url(r'^autocomplete/', include(autocomplete.urls)),

    # Uncomment the admin/doc line below to enable admin documentation:
    #(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

      

    #########################
    #
    #         Pages
    #
    #########################
    (r'^index/','fcst_accuracy.views.index'),
    (r'^fa/main/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)','fcst_accuracy.views.main'),

    # testing new interface
    (r'^test/','fcst_accuracy.views.test'),

    #########################
    #
    # Revenue Accounting data
    #
    #########################
    (r'^radata/new/','radata.views.new'),
    (r'^radata/thankyou/','radata.views.thankyou'),

    #########################
    #
    #  Chart data (csv)
    #
    #########################
    (r'^csv/book/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',
      'getcsv.views.book'),
    (r'^csv/book_cmpt/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cmpt>.*)',
      'getcsv.views.book_cmpt'),
    (r'^csv/rev/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)',
      'getcsv.views.rev'),
    (r'^csv/rev_future/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)',
      'getcsv.views.rev_future'),
    (r'^csv/rev_cmpt/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cmpt>.*)',
      'getcsv.views.rev_cmpt'),
    (r'^csv/book_past/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})/(?P<cmpt>[A-Z]{1})?-(?P<cls>[A-Z]{1})?$',
      'getcsv.views.book_past'),
    (r'^csv/book_past/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})/(?P<cmpt>[A-Z]{1})?-(?P<cls>[A-Z]{1})?/(?P<dow>\d*)$',
      'getcsv.views.book_past'),
    (r'^csv/book_future/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})/(?P<cmpt>[A-Z]{1})?-(?P<cls>[A-Z]{1})?/(?P<dow>(\d)*)',
      'getcsv.views.book_future'),
    (r'^csv/class_mix/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',
      'getcsv.views.class_mix'),
    (r'^csv/yield/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)',
      'getcsv.views.yield_'),
    (r'^csv/yield_future/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)',
      'getcsv.views.yield_future'),
    (r'^csv/book_yield/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cmpt>[A-Z]{1})?-(?P<cls>[A-Z]{1})?/(?P<dow>(\d)*)',
      'getcsv.views.book_yield'),

    ############################
    #
    #  Chart data (data table)
    #
    ############################
    # FIXME: should be removed later if does not work
    (r'^dt/class_mix/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)',
      'getdt.views.class_mix'),


    #########################
    #
    #  Chart data for flash  
    #
    #########################
    # forecast error
    (r'^fa/cd/cons_err/bydptdt/(?P<err_type>.*)/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.cd_cons_err_by_dptdt'),
    (r'^fa/cd/uncons_err/bydptdt/(?P<err_type>.*)/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.cd_uncons_err_by_dptdt'),
    (r'^fa/cd/cons_err/bydaysprior/(?P<err_type>.*)/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.cd_cons_err_by_daysprior'),
    (r'^fa/cd/uncons_err/bydaysprior/(?P<err_type>.*)/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.cd_uncons_err_by_daysprior'),
    # actual values
    (r'^fa/cd/cons_aval/bydptdt/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.cd_cons_aval_by_dptdt'),
    (r'^fa/cd/uncons_aval/bydptdt/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.cd_uncons_aval_by_dptdt'),
    #(r'fa/cd/cons_aval/bydaysprior/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
    #  'fcst_accuracy.views.cd_cons_aval_by_daysprior'),
    #(r'fa/cd/uncons_aval/bydaysprior/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
    #  'fcst_accuracy.views.cd_uncons_aval_by_daysprior'),
    # forecasted values
    (r'fa/cd/cons_fval/bydptdt/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.cd_cons_fval_by_dptdt'),
    (r'fa/cd/uncons_fval/bydptdt/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.cd_uncons_fval_by_dptdt'),
    #(r'fa/cd/cons_fval/bydptdt/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
    #  'fcst_accuracy.views.cd_cons_fval_by_daysprior'),
    #(r'fa/cd/uncons_fval/bydptdt/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
    #  'fcst_accuracy.views.cd_uncons_fval_by_daysprior'),
    # booked values
    (r'fa/cd/cons_booked/bydptdt/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.cd_cons_booked_by_dptdt'),
    (r'fa/cd/uncons_booked/bydptdt/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.cd_uncons_booked_by_dptdt'),
    # ljung-box p-value
    (r'fa/cd/cons_lbpval/(?P<err_type>.*)/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.cd_cons_lbpval_by_daysprior'),
    (r'fa/cd/uncons_lbpval/(?P<err_type>.*)/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.cd_uncons_lbpval_by_daysprior'),

    #########################
    #
    #     AJAX content
    #
    ######################### 
    # FIXME: move all ajax staff 
    # FIXME: to ajax application   
    (r'^fa/ajax/orgn/',\
      'fcst_accuracy.ajax_views.orgn'),
    (r'^fa/ajax/dstn/(?P<orgn>.*)',\
      'fcst_accuracy.ajax_views.dstn'),
    (r'^fa/ajax/fltnum/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)',\
      'fcst_accuracy.ajax_views.fltnum'),
    (r'^fa/ajax/cmpt',\
      'fcst_accuracy.ajax_views.cmpt'),
    (r'^fa/ajax/cls/(?P<cmpt>.)',\
      'fcst_accuracy.ajax_views.cls'),

    #######################################################
    #
    #  General AJAX queries (not specific to application)
    #
    #######################################################
    (r'^ajax/place/',\
      'ajax.views.place'),   
    (r'^ajax/legs',\
      'ajax.views.legs'),
      
    #(r'^admin/ajax/fa_markets',\
    #  'admin.views.fa_markets'),
    #(r'^admin/ajax/split_history',\
    #  'admin.views.split_history'),

    #(r'^fa/ajax/cls/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cmpt>.*)',\
    #  'fcst_accuracy.views.ajax_cls'),
    (r'^fa/ajax/cls_stats/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.ajax_cls_stats'),
    (r'^fa/ajax/cls_stat_cnt/(?P<type>.*)/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.ajax_cls_stat_cnt'), 
    (r'^fa/ajax/tabs/(?P<tab_name>.*)/(?P<orgn>.*)/(?P<dstn>.*)/(?P<fltnum>.*)/(?P<cls>.*)/(?P<daysprior>.*)/(?P<dfrom>.*)/(?P<dto>.*)',\
      'fcst_accuracy.views.ajax_tab_content'),  

    #########################
    #
    #  Widgets (Confluence)
    #
    #########################
    (r'^widget/consfnldmd_cmpt_ts/(?P<orgn>[A-Z]{3})-(?P<dstn>[A-Z]{3})-(?P<fltnum>\d{5})-(?P<cmpt>[J|Y]{1}).xml',\
      'widgets.views.consfnldmd_cmpt_ts'),

    #########################
    #
    #    Route monitoring
    #
    #########################
    (r'^route/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',\
      'route.views.index'),
    (r'^route_book/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',\
      'route.views.book'),
    (r'^route_book_j/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',\
      'route.views.book_j'),
    (r'^route_book_y/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',\
      'route.views.book_y'),
    (r'^route_revenue/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',\
      'route.views.revenue'),
    (r'^route_revenue_j/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',\
      'route.views.revenue_j'),
    (r'^route_revenue_y/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',\
      'route.views.revenue_y'),
    (r'^route_class_corr/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',\
      'route.views.class_corr'),
    (r'^route_db_stat/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',\
      'route.views.db_stat'),
    (r'^route_forecast/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',\
      'route.views.forecast'),
    (r'^route_class_mix/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',\
      'route.views.class_mix'),
    (r'^route_aircraft_change/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',\
      'route.views.aircraft_change'),
    (r'^route_yield/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',\
      'route.views.yield_'),
    (r'^route_summary/(?P<orgn>[A-Z]{3})/(?P<dstn>[A-Z]{3})/(?P<fltnum>\d{5})',\
      'route.views.summary'),

    #########################################
    #
    #  Network monitoring (based on RA data)
    #
    #########################################
    (r'network/$',\
      'network.views.index'),
    (r'network/json/airports',\
      'network.views.json_airports'),

    #########################################
    #
    #  Split history (for planning windows).
    #
    #########################################
    (r'sh/$',\
      'sh.views.index'),
    (r'sh/csv/first_pc',\
      'sh.views.csv_first_pc'),
    (r'sh/csv/rev',\
      'sh.views.csv_rev'),
    (r'sh/csv/npax',\
      'sh.views.csv_npax'),
    (r'sh/csv/yield',\
      'sh.views.csv_yield'),
    (r'sh/csv/nedge',\
      'sh.views.csv_nedge'),
    (r'sh/csv/p2p_npax_ratio',\
      'sh.views.csv_p2p_npax_ratio'),

    #########################################
    #
    #  SigOD list application
    #
    #########################################
    (r'sigod/$',\
      'sigod.views.index'),
    (r'sigod/thankyou$',\
      'sigod.views.thankyou'),
    (r'sigod/json/revenue/$',\
      'sigod.views.json_revenue'),  
    (r'sigod/json/revenue/(?P<dfrom>.*)/(?P<dto>.*)/',\
      'sigod.views.json_revenue'),
    (r'sigod/json/num_pax/$',\
      'sigod.views.json_numpax'),  
    (r'sigod/json/num_pax/(?P<dfrom>.*)/(?P<dto>.*)/',\
      'sigod.views.json_num_pax'),
    (r'sigod/json/mindt/$',\
      'sigod.views.json_mindt'),
    (r'sigod/json/maxdt/$',\
      'sigod.views.json_maxdt'),  

    ###################
    #
    #  Effectiviness
    #
    ###################
    (r'eff/$',\
      'eff.views.index'),
    (r'eff/json/flights',
      'eff.views.json_flights'),
    (r'eff/json/dates',
      'eff.views.json_dates'),
    (r'eff/csv/ab_rev/(?P<leg>.*)',
      'eff.views.csv_ab_rev'),
    (r'eff/csv/eff/(?P<leg>.*)',
      'eff.views.csv_eff'),
    (r'eff/csv/mv/(?P<leg>.*)',
      'eff.views.csv_mv'),

    #########################################
    #
    #    OD monitoring
    #
    #########################################
    #(r'^od/competition',\
    #  'od.views.competition'),
    #(r'^od/competition/results',\
    #  'od.views.competition_results'),
    #(r'^od/(?P<hop1>[A-Z]{3})/(?P<hop2>[A-Z]{3})/(?P<hop3>[A-Z]{3})/(?P<cls>[A-Z]{1})?',\
    #  'od.views.stats'),

    #########################
    #
    #      Ad-hoc tools
    #
    #########################
    (r'^demand_shift_form/',\
      'ahtools.views.demand_shift_form'),

    #########################
    #
    #      DB manager
    #
    #########################
    (r'^dbmanager/index',\
      'dbmanager.views.index'),
    (r'^dbmanager/split_history_upload',\
      'dbmanager.views.split_history_upload'),

    #########################
    #
    #           Media
    #
    #########################
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
)





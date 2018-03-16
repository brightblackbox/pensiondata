from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from pensiondata.views import HomeView, PlanListView, PlanDetailView, export_file, GovernmentDetailView, generate_reporting_table

admin.autodiscover()

urlpatterns = [
    url(r'^', include('common.urls')),
    url(r'^$',  PlanListView.as_view(), name='home'),
    url(r'^pension/', include('pensiondata.urls')),
    url(r'^plan-detail/(?P<PlanID>\d+)$', PlanDetailView.as_view(), name='plan-detail'),
    url(r'^government-detail/(?P<GovernmentID>\d+)$', GovernmentDetailView.as_view(), name='government-detail'),
    url(r'^plan-detail/ExportFile$', export_file),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^generate_reporting_table/$', generate_reporting_table, name='generate_reporting_table'),
]

urlpatterns += [url(r'^nested_admin/', include('nested_admin.urls'))]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

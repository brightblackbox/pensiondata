from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from pensiondata.views import HomeView, PlanListView, PlanDetailView

admin.autodiscover()

urlpatterns = [
    url(r'^', include('common.urls')),
    url(r'^$', PlanListView.as_view(), name='home'),
    url(r'^plan-detail/(?P<PlanID>\d+)$', PlanDetailView.as_view(), name='plan-detail'),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^admin/', include(admin.site.urls)),
]

urlpatterns += [url(r'^nested_admin/', include('nested_admin.urls'))]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns




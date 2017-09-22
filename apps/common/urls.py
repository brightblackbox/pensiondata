from datetime import datetime
import django.contrib.auth.views as auth_views
from django.conf.urls import url

from .views import ContactView, AboutView
from .forms import BootstrapAuthenticationForm

urlpatterns = [

    url(r'^contact/$', ContactView.as_view(), name='contact'),
    url(r'^about/$', AboutView.as_view(), name='about'),
    # url(r'^seed', seed, name='seed'),
    url(r'^login/$',
        auth_views.login,
        {
            'template_name': 'login.html',
            'authentication_form': BootstrapAuthenticationForm,
            'extra_context':
            {
                'title': 'Log in',
                'year': datetime.now().year,
            }
        },
        name='login'),

    url(r'^logout/$', auth_views.logout, {'next_page': '/', }, name='logout'),
]
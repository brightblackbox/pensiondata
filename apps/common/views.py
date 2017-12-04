# from app.models import Choice, Poll
from datetime import datetime
from django.views.generic import TemplateView


class ContactView(TemplateView):
    """Renders the contact page."""
    template_name = 'contact.html'

    def get_context_data(self, **kwargs):
        context = super(ContactView, self).get_context_data(**kwargs)
        context['message'] = 'Your contact page.'
        return context


class AboutView(TemplateView):
    """Renders the about page."""
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        context = super(AboutView, self).get_context_data(**kwargs)
        context['message'] = 'Your application description page.'
        return context

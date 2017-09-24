from django.http import HttpResponse
from django.views.generic import TemplateView, DetailView
from django.views.generic.list import ListView
from django_tables2 import RequestConfig
from django.shortcuts import get_object_or_404

from .models import Plan, PlanAnnualAttribute, CensusAnnualAttribute
from .tables import PlanTable, PlanAnnualAttrTable, CensusAnnualAttrTable


class HomeView(TemplateView):

    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['plans'] = Plan.objects.all().order_by('-id')[:10]
        return context


class PlanListView(ListView):

    model = Plan

    # paginate_by = 10
    context_object_name = 'plans'
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(PlanListView, self).get_context_data(**kwargs)
        context['nav_plan'] = True
        table = PlanTable(Plan.objects.all().order_by('display_name'))
        RequestConfig(self.request, paginate={'per_page': 10}).configure(table)
        context['table'] = table
        return context


class PlanDetailView(DetailView):

    model = Plan
    context_object_name = 'plan'
    template_name = 'plan-detail.html'
    pk_url_kwarg = "PlanID"

    # def get_object(self, queryset=None):
    #     if 'pk' in self.kwargs:
    #         return get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
    #     else:
    #         return None
    #
    def get_context_data(self, **kwargs):
        context = super(PlanDetailView, self).get_context_data(**kwargs)

        table = CensusAnnualAttrTable(CensusAnnualAttribute.objects.filter(plan=self.object).order_by('-year'))
        RequestConfig(self.request, paginate={'per_page': 30}).configure(table)
        context['table'] = table
        return context


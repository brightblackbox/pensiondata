from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView, DetailView
from django.views.generic.list import ListView
from django_tables2 import RequestConfig
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

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
    paginate_by = 10
    context_object_name = 'plans'
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(PlanListView, self).get_context_data(**kwargs)
        context['nav_plan'] = True

        if self.request.GET.get('search') is None or self.request.GET.get('search') == '':
            table = PlanTable(Plan.objects.all().order_by('display_name'))
        else:
            table = PlanTable(Plan.objects.all().filter(display_name__icontains = self.request.GET.get('search')).order_by('display_name'))

        RequestConfig(self.request, paginate={'per_page': 10}).configure(table)
        context['table'] = table
        return context


class PlanDetailView(DetailView):
    model = Plan
    context_object_name = 'plan'
    template_name = 'plan-detail.html'
    pk_url_kwarg = "PlanID"

    def get_context_data(self, **kwargs):
        context = super(PlanDetailView, self).get_context_data(**kwargs)

        table = CensusAnnualAttrTable(CensusAnnualAttribute.objects.filter(plan=self.object).order_by('-year'))
        # table = PlanAnnualAttrTable(PlanAnnualAttribute.objects.select_related().filter(plan=self.object).order_by('-year'))
        RequestConfig(self.request, paginate={'per_page': 30}).configure(table)
        # RequestConfig(self.request, paginate=False).configure(table)
        context['table'] = table
        return context


# NOTE:  This part should be changed to Class based View later
@staff_member_required
def delete_plan_annual_attr(request):
    attr_id = request.POST.get('attr_id')
    try:
        obj = PlanAnnualAttribute.objects.get(id=attr_id)
        obj.delete()
        return JsonResponse({'result': 'success'})
    except PlanAnnualAttribute.DoesNotExist:
        return JsonResponse({'result': 'fail', 'msg': 'There is no matching record.'})


@staff_member_required
def edit_plan_annual_attr(request):
    attr_id = request.POST.get('attr_id')
    new_val = request.POST.get('new_val')
    try:
        obj = PlanAnnualAttribute.objects.get(id=attr_id)
        obj.attribute_value = new_val
        obj.save()
        return JsonResponse({'result': 'success'})
    except PlanAnnualAttribute.DoesNotExist:
        return JsonResponse({'result': 'fail', 'msg': 'There is no matching record.'})

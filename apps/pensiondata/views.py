from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView, DetailView
from django.views.generic.list import ListView
from django_tables2 import RequestConfig
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.signals import pre_save, pre_delete, post_save, post_delete

from .models import Plan, PlanAnnualAttribute, CensusAnnualAttribute, PlanAttribute
from .tables import PlanTable, PlanAnnualAttrTable, CensusAnnualAttrTable
from .signals import recalculate

from moderation import moderation
from moderation.helpers import automoderate


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


# NOTE:  This part should be changed/optimized to Class based View later
@staff_member_required
def delete_plan_annual_attr(request):
    attr_id = request.POST.get('attr_id')
    try:
        obj = PlanAnnualAttribute.objects.get(id=attr_id)
        # obj.delete()
        moderation.pre_delete_handler(sender=PlanAnnualAttribute, instance=obj)
        moderation.post_delete_handler(sender=PlanAnnualAttribute, instance=obj)
        automoderate(obj, request.user)

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

        post_save.disconnect(recalculate, sender=PlanAnnualAttribute)
        moderation.pre_save_handler(sender=PlanAnnualAttribute, instance=obj)
        obj.save()
        moderation.post_save_handler(sender=PlanAnnualAttribute, instance=obj, created=False)
        post_save.connect(recalculate, sender=PlanAnnualAttribute)

        automoderate(obj, request.user)
        return JsonResponse({'result': 'success'})
    except PlanAnnualAttribute.DoesNotExist:
        return JsonResponse({'result': 'fail', 'msg': 'There is no matching record.'})


@staff_member_required
def add_plan_annual_attr(request):
    attr_id = request.POST.get('attr_id')
    plan_id = request.POST.get('plan_id')
    year = request.POST.get('year')
    value = request.POST.get('value', '0')

    try:
        plan_attr_obj = PlanAttribute.objects.get(id=attr_id)
        plan_obj = Plan.objects.get(id=plan_id)

        try:
            # check if already exists
            old_obj = PlanAnnualAttribute.objects.get(
                plan=plan_obj,
                year=year,
                plan_attribute=plan_attr_obj
            )
            return JsonResponse({'result': 'fail', 'msg': 'Already exists.'})

        except PlanAnnualAttribute.DoesNotExist:
            pass
        except PlanAnnualAttribute.MultipleObjectsReturned:
            return JsonResponse({'result': 'fail', 'msg': 'Already exists.'})

        new_plan_annual_attr_obj = PlanAnnualAttribute(
            plan=plan_obj,
            year=year,
            plan_attribute=plan_attr_obj,
            attribute_value=value
        )

        post_save.disconnect(recalculate, sender=PlanAnnualAttribute)
        moderation.pre_save_handler(sender=PlanAnnualAttribute, instance=new_plan_annual_attr_obj)
        new_plan_annual_attr_obj.save()
        moderation.post_save_handler(sender=PlanAnnualAttribute, instance=new_plan_annual_attr_obj, created=True)
        post_save.connect(recalculate, sender=PlanAnnualAttribute)

        automoderate(new_plan_annual_attr_obj, request.user)

        return JsonResponse({'result': 'success'})
    except Exception as e:
        print(e)
        return JsonResponse({'result': 'fail', 'msg': 'Something went wrong.'})

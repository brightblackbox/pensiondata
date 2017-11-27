from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView, DetailView
from django.views.generic.list import ListView
from django_tables2 import RequestConfig
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from django.db.models import F
import json

from .models import Plan, PlanAnnualAttribute, AttributeCategory, PlanAttribute, DataSource, \
                    Government, GovernmentAnnualAttribute, GovernmentAttribute
from .tables import PlanTable
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
    template_name = 'plan_detail.html'
    pk_url_kwarg = "PlanID"

    def get_context_data(self, **kwargs):
        context = super(PlanDetailView, self).get_context_data(**kwargs)
        plan = self.object

        plan_annual_objs = PlanAnnualAttribute.objects \
            .filter(plan=plan) \
            .select_related('plan_attribute') \
            .select_related('plan_attribute__attribute_category') \
            .select_related('plan_attribute__data_source')

        year_list = plan_annual_objs.order_by('year').values('year').distinct()

        plan_annual_data \
            = plan_annual_objs \
            .values('id',
                    'year',
                    'plan_attribute__id',
                    'plan_attribute__multiplier',
                    'plan_attribute__data_source__id',
                    'plan_attribute__attribute_category__id',
                    'attribute_value') \
            .annotate(
                attribute_id=F('plan_attribute__id'),
                multiplier=F('plan_attribute__multiplier'),
                data_source_id=F('plan_attribute__data_source__id'),
                category_id=F('plan_attribute__attribute_category__id')
            )

        attr_list = plan_annual_objs.values(
            'plan_attribute__id',
            'plan_attribute__name',
            'plan_attribute__data_source__id',
            'plan_attribute__data_source__name',
            'plan_attribute__attribute_category__id',
            'plan_attribute__attribute_category__name'
        ).annotate(
            attribute_id=F('plan_attribute__id'),
            attribute_name=F('plan_attribute__name'),
            data_source_id=F('plan_attribute__data_source__id'),
            data_source_name=F('plan_attribute__data_source__name'),
            category_id=F('plan_attribute__attribute_category__id'),
            category_name=F('plan_attribute__attribute_category__name')
        ).distinct().order_by('category_name', 'attribute_name')

        category_list = plan_annual_objs.values(
            'plan_attribute__attribute_category__id',
            'plan_attribute__attribute_category__name'
        ).annotate(
            id=F('plan_attribute__attribute_category__id'),
            name=F('plan_attribute__attribute_category__name')
        ).distinct().order_by('name')

        datasource_list = DataSource.objects.order_by('name')

        context['attr_list'] = attr_list
        context['category_list'] = category_list
        context['datasource_list'] = datasource_list
        context['year_list'] = year_list

        context['plan_annual_data'] = json.dumps(list(plan_annual_data))

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
    is_from_source = request.POST.get('is_from_source')
    if is_from_source == '1':
        is_from_source = True
    elif is_from_source == '0':
        is_from_source = False
    else:
        is_from_source = None

    try:
        obj = PlanAnnualAttribute.objects.get(id=attr_id)
        obj.attribute_value = new_val
        obj.is_from_source = is_from_source

        # disconnect signal becuase of moderation
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
    is_from_source = request.POST.get('is_from_source')

    if is_from_source == '1':
        is_from_source = True
    elif is_from_source == '0':
        is_from_source = False
    else:
        is_from_source = None

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
            attribute_value=value,
            is_from_source=is_from_source
        )

        # disconnect signal becuase of moderation
        post_save.disconnect(recalculate, sender=PlanAnnualAttribute)
        moderation.pre_save_handler(sender=PlanAnnualAttribute, instance=new_plan_annual_attr_obj)
        new_plan_annual_attr_obj.save()
        moderation.post_save_handler(sender=PlanAnnualAttribute, instance=new_plan_annual_attr_obj, created=True)
        post_save.connect(recalculate, sender=PlanAnnualAttribute)

        automoderate(new_plan_annual_attr_obj, request.user)

        return JsonResponse({'result': 'success'})
    except Exception as e:
        return JsonResponse({'result': 'fail', 'msg': 'Something went wrong.'})


@staff_member_required
def delete_gov_annual_attr(request):
    attr_id = request.POST.get('attr_id')
    try:
        obj = GovernmentAnnualAttribute.objects.get(id=attr_id)
        obj.delete()

        return JsonResponse({'result': 'success'})
    except GovernmentAnnualAttribute.DoesNotExist:
        return JsonResponse({'result': 'fail', 'msg': 'There is no matching record.'})


@staff_member_required
def edit_gov_annual_attr(request):
    attr_id = request.POST.get('attr_id')
    new_val = request.POST.get('new_val')
    is_from_source = request.POST.get('is_from_source')
    if is_from_source == '1':
        is_from_source = True
    elif is_from_source == '0':
        is_from_source = False
    else:
        is_from_source = None

    try:
        obj = GovernmentAnnualAttribute.objects.get(id=attr_id)
        obj.attribute_value = new_val
        obj.is_from_source = is_from_source
        obj.save()

        return JsonResponse({'result': 'success'})
    except GovernmentAnnualAttribute.DoesNotExist:
        return JsonResponse({'result': 'fail', 'msg': 'There is no matching record.'})


@staff_member_required
def add_gov_annual_attr(request):
    attr_id = request.POST.get('attr_id')
    gov_id = request.POST.get('gov_id')
    year = request.POST.get('year')
    value = request.POST.get('value', '0')
    is_from_source = request.POST.get('is_from_source')

    if is_from_source == '1':
        is_from_source = True
    elif is_from_source == '0':
        is_from_source = False
    else:
        is_from_source = None

    try:
        gov_attr_obj = GovernmentAttribute.objects.get(id=attr_id)
        gov_obj = Government.objects.get(id=gov_id)

        try:
            # check if already exists
            old_obj = GovernmentAnnualAttribute.objects.get(
                government=gov_obj,
                year=year,
                government_attribute=gov_attr_obj
            )
            return JsonResponse({'result': 'fail', 'msg': 'Already exists.'})

        except PlanAnnualAttribute.DoesNotExist:
            pass
        except PlanAnnualAttribute.MultipleObjectsReturned:
            return JsonResponse({'result': 'fail', 'msg': 'Already exists.'})

        new_gov_annual_attr_obj = GovernmentAnnualAttribute(
            government=gov_obj,
            year=year,
            government_attribute=gov_attr_obj,
            attribute_value=value,
            is_from_source=is_from_source
        )

        new_gov_annual_attr_obj.save()

        return JsonResponse({'result': 'success'})
    except Exception as e:
        return JsonResponse({'result': 'fail', 'msg': 'Something went wrong.'})


def save_checklist(request):
    """
    save column-visiblity status in session.
    """
    try:

        request.session['category_checked_states'] = list(map(int, request.POST.getlist('category_checked_states[]')))
        request.session['datasource_checked_states'] = list(map(int, request.POST.getlist('datasource_checked_states[]')))
        request.session['attr_checked_states'] = list(map(int, request.POST.getlist('attr_checked_states[]')))

        return JsonResponse({'result': 'success'})
    except:
        return JsonResponse({'result': 'fail', 'msg': 'Something went wrong.'})


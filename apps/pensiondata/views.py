from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView, DetailView
from django.views.generic.list import ListView
from django_tables2 import RequestConfig
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from django.db.models import F, Case, When, Value, BooleanField
import json
import os
from pprint import pprint
import psycopg2
import traceback
import csv
import sys
import time
import pandas
from wsgiref.util import FileWrapper
from celery.result import AsyncResult

from .models import Plan, PlanAnnualAttribute, AttributeCategory, PlanAttribute, DataSource, PlanAnnual, \
    Government, GovernmentAnnualAttribute, GovernmentAttribute, PresentationExport, ExportGroup, \
    PensionMapData, PensionChartData, PlanAnnualMasterAttribute, PlanAttributeMaster, PlanMasterAttributeNames

from .tables import PlanTable
from .signals import recalculate
from .tasks import task_reporting_table

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

        search = self.request.GET.get('search')
        if search is None or search == '':
            table = PlanTable(Plan.objects.all().order_by('display_name'))
        else:
            table = Plan.objects.all()

            splited_search = search.split(' ')
            if len(splited_search) > 1:
                for i in splited_search:
                    table = table.filter(display_name__icontains=i)
            else:
                table = table.filter(display_name__icontains=search)

            table = PlanTable(table.order_by('display_name'))

        RequestConfig(self.request, paginate={'per_page': 10}).configure(table)
        context['table'] = table
        context['search'] = self.request.GET.get('search', '')
        return context


class PlanDetailView(DetailView):

    model = Plan
    context_object_name = 'plan'
    template_name = 'plan_detail.html'
    pk_url_kwarg = "PlanID"

    # noinspection PyUnreachableCode
    def get_context_data(self, **kwargs):

        year_from = self.request.POST.get('from', '')
        year_to = self.request.POST.get('to', '2021')
        # unfiltered = self.request.POST.get('unfiltered', 'off') == 'on'
        unfiltered = True
        reset_attr_states = self.request.POST.get('reset_attr_states', '0') == '1'

        context = super(PlanDetailView, self).get_context_data(**kwargs)
        plan = self.object

        # constants for default attribute IDs that need to be fetched
        CONTRIB_STATE_EMPL = 1
        CONTRIB_LOCAL_EMPL = 2
        CONTRIB_LOCAL_GOVT = 4
        TOTAL_CONTRIB_STATE = 5
        TOT_BEN_PAYM = 16
        ADMIN_EXP = 22
        TOT_CASH_SEC = 42
        TOT_ACT_MEM = 43


        if unfiltered:
            plan_annual_objs = PlanAnnualAttribute.objects \
                .select_related('plan_attribute') \
                .select_related('plan_attribute__attribute_category') \
                .select_related('plan_attribute__data_source') \
                .filter(plan=plan)
            plan_attribute_name_field = 'plan_attribute__name'

        else:
            plan_annual_objs = PlanAnnualMasterAttribute.objects \
                .select_related('plan_attribute') \
                .select_related('plan_attribute__attribute_category') \
                .select_related('plan_attribute__data_source') \
                .select_related('master_attribute') \
                .filter(plan=plan)
            plan_attribute_name_field = 'master_attribute__name'


        # getting columns from the POST request
        if self.request.method == 'POST' and reset_attr_states == False:
            # print ("This is a POST request")
            selected_attr_list = self.request.POST.getlist('attr_checked_states[]')
        # getting columns from session
        elif (self.request.session.get('plan_column_state')) and reset_attr_states == False:
            selected_attr_list = self.request.session['plan_column_state']['attr']
        # using default columns if got nothing from POST request or saved session
        elif unfiltered:
            selected_attr_list = [CONTRIB_STATE_EMPL, \
                                  CONTRIB_LOCAL_EMPL, \
                                  CONTRIB_LOCAL_GOVT, \
                                  TOTAL_CONTRIB_STATE, \
                                  TOT_BEN_PAYM, \
                                  ADMIN_EXP, \
                                  TOT_CASH_SEC, \
                                  TOT_ACT_MEM]
        else:
            #TODO: Check whether this is necessary. Right now this just ensures that *some* attributes are selected.
            selected_attr_list = [_.plan_attribute_id for _ in plan_annual_objs]

        plan_annual_objs_filtered_attributes = plan_annual_objs.filter(plan_attribute_id__in=selected_attr_list)

        year_list = plan_annual_objs_filtered_attributes.filter(
            year__range=(year_from or '1950', year_to or '2050')
        ).order_by('year').values('year').distinct()

        plan_annual_data = plan_annual_objs_filtered_attributes \
                            .values('id',
                                    'year',
                                    'plan_attribute__id',
                                    'plan_attribute__multiplier',
                                    'plan_attribute__data_source__id',
                                    'plan_attribute__attribute_category__id',
                                    'attribute_value',
                                    'plan_attribute__datatype'
                                    ) \
                            .annotate(
                                attribute_id=F('plan_attribute__id'),
                                multiplier=F('plan_attribute__multiplier'),
                                data_source_id=F('plan_attribute__data_source__id'),
                                category_id=F('plan_attribute__attribute_category__id')
                            )

        full_attr_list = plan_annual_objs.values(
            'plan_attribute__id',
            plan_attribute_name_field,
            'plan_attribute__data_source__id',
            'plan_attribute__data_source__name',
            'plan_attribute__attribute_category__id',
            'plan_attribute__attribute_category__name'
        ).annotate(
            attribute_id=F('plan_attribute__id'),
            attribute_name=F(plan_attribute_name_field),
            data_source_id=F('plan_attribute__data_source__id'),
            data_source_name=F('plan_attribute__data_source__name'),
            category_id=F('plan_attribute__attribute_category__id'),
            category_name=F('plan_attribute__attribute_category__name'),
            # 'selected' is helpful in checking the options in the checkboxes
            selected=Case(
                When(plan_attribute_id__in=selected_attr_list, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).distinct().order_by('category_name', 'attribute_name')

        category_list = plan_annual_objs.values(
            'plan_attribute__attribute_category__id',
            'plan_attribute__attribute_category__name'
        ).annotate(
            id=F('plan_attribute__attribute_category__id'),
            name=F('plan_attribute__attribute_category__name'),
            # 'selected' is helpful in checking the options in the checkboxes
            selected=Case(
                When(plan_attribute_id__in=selected_attr_list, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).distinct().order_by('name','-selected') # -selected is to put True values on top so that later we can remove any False values (which also has True value somewhere)

        category_list=category_list.distinct('name') # this is to remove the selected=False values where selected=True is already there

        # making a list of selected_data_sources
        # (not doing it inline (in the datasource_list query) to avoid exceptions in case the selected attribute
        # is not  present in the universal list for some reason)
        selected_data_sources = []
        get_attr_ids = [attr_id for attr_id in selected_attr_list]
        for paid in PlanAttribute.objects.filter(id__in=get_attr_ids).values_list('data_source_id'):
            selected_data_sources.append(paid[0])
        # removing any duplicates from the list
        selected_data_sources = list(set(selected_data_sources))

        # fetching the data source list and marking selected based on selected attribute list
        datasource_list = DataSource.objects.all().exclude(private=True).annotate( \
            # 'selected' is helpful in checking the options in the checkboxes
            selected=Case(
                When(id__in=selected_data_sources, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).order_by('name')

        presentations_exports = ExportGroup.objects.filter(active=True)

        # context['attr_list'] = attr_list
        context['full_attr_list'] = full_attr_list
        context['category_list'] = category_list
        context['datasource_list'] = datasource_list
        context['year_list'] = year_list
        context['year_from'] = year_from
        context['year_to'] = year_to
        context['year_range'] = range(1932, 2022)
        context['presentations_exports'] = presentations_exports
        context['unfiltered'] = unfiltered

        context['plan_annual_data'] = json.dumps(list(plan_annual_data))

        return context

    # this is to enable the DetailView to process POST requests (when the user selects different checkboxes than default)
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        result = self.render_to_response(context=context)
        return result


class GovernmentDetailView(DetailView):

    model = Government
    context_object_name = 'government'
    template_name = 'government_detail.html'
    pk_url_kwarg = "GovernmentID"

    def get_context_data(self, **kwargs):
        context = super(GovernmentDetailView, self).get_context_data(**kwargs)

        year_from = self.request.POST.get('from', '')
        year_to = self.request.POST.get('to', '2021')

        CONTRIB_STATE_EMPL = 1
        CONTRIB_LOCAL_EMPL = 2
        CONTRIB_LOCAL_GOVT = 4
        TOTAL_CONTRIB_STATE = 5
        TOT_BEN_PAYM = 16
        ADMIN_EXP = 22
        TOT_CASH_SEC = 42
        TOT_ACT_MEM = 43

        selected_attr_list = []
        if self.request.method == 'POST':
            print ("This is a POST request")
            selected_attr_list = self.request.POST.getlist('attr_checked_states[]')
        # getting columns from session
        elif (self.request.session.get('government_column_state')):
            selected_attr_list = self.request.session['government_column_state']['attr']
        # using default columns if got nothing from POST request or saved session
        else:
            selected_attr_list = [
                CONTRIB_STATE_EMPL, CONTRIB_LOCAL_EMPL, CONTRIB_LOCAL_GOVT, TOTAL_CONTRIB_STATE, TOT_BEN_PAYM,
                ADMIN_EXP, TOT_CASH_SEC, TOT_ACT_MEM
            ]

        government = self.object

        government_annual_objs = GovernmentAnnualAttribute.objects \
            .select_related('government_attribute') \
            .filter(government=government)

        government_annual_objs_filtered_attributes = government_annual_objs.filter(
            government_attribute_id__in=selected_attr_list)

        year_list = government_annual_objs_filtered_attributes.filter(
            year__range=(year_from or '1950', year_to or '2050')
        ).order_by('year').values('year').distinct()

        government_annual_data = government_annual_objs_filtered_attributes\
            .values(
                'id',
                'year',
                'government_attribute__id',
                'government_attribute__multiplier',
                'government_attribute__data_source__id',
                'government_attribute__attribute_category__id',
                'attribute_value',
                'government_attribute__datatype').\
            annotate(
                attribute_id=F('government_attribute__id'),
                multiplier=F('government_attribute__multiplier'),
                data_source_id=F('government_attribute__data_source__id'),
                category_id=F('government_attribute__attribute_category__id')
            )

        category_list = government_annual_objs.values(
            'government_attribute__attribute_category__id',
            'government_attribute__attribute_category__name'
        ).annotate(
            id=F('government_attribute__attribute_category__id'),
            name=F('government_attribute__attribute_category__name'),
            # 'selected' is helpful in checking the options in the checkboxes
            selected=Case(When(government_attribute_id__in=selected_attr_list, then=Value(True)), default=Value(False),
                          output_field=BooleanField())
        ).distinct().order_by('name', '-selected')

        category_list = category_list.distinct('name')

        full_attr_list = government_annual_objs.values(
            'government_attribute__id',
            'government_attribute__name',
            'government_attribute__data_source__id',
            'government_attribute__data_source__name',
            'government_attribute__attribute_category__id',
            'government_attribute__attribute_category__name'
        ).annotate(
            attribute_id=F('government_attribute__id'),
            attribute_name=F('government_attribute__name'),
            data_source_id=F('government_attribute__data_source__id'),
            data_source_name=F('government_attribute__data_source__name'),
            category_id=F('government_attribute__attribute_category__id'),
            category_name=F('government_attribute__attribute_category__name'),
            # 'selected' is helpful in checking the options in the checkboxes
            selected=Case(
                When(government_attribute_id__in=selected_attr_list, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).distinct().order_by('category_name', 'attribute_name')

        selected_data_sources = []
        get_attr_ids = [attr_id for attr_id in selected_attr_list]
        for paid in GovernmentAttribute.objects.filter(id__in=get_attr_ids).values_list('data_source_id'):
            selected_data_sources.append(paid[0])
        # removing any duplicates from the list
        selected_data_sources = list(set(selected_data_sources))

        datasource_list = DataSource.objects.all().exclude(private=True).annotate( \
            # 'selected' is helpful in checking the options in the checkboxes
            selected=Case(
                When(id__in=selected_data_sources, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).order_by('name')

        context['full_attr_list'] = full_attr_list
        context['category_list'] = category_list
        context['year_list'] = year_list
        context['year_from'] = year_from
        context['year_to'] = year_to
        context['year_range'] = range(1932, 2022)
        context['datasource_list'] = datasource_list
        context['government_annual_data'] = json.dumps(list(government_annual_data))

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context=context)


def api_map_search(request, state):

    if len(request.GET.get('employer', '')) < 3:
        return JsonResponse({'success': False, 'error': 'Search string must be a minimum length of 3 characters.'})

    results = Government.objects.filter(
        state__state_abbreviation = state,
        name__icontains = request.GET['employer']
    )

    data = {'governments': [], 'success': True}

    if len(results) == 0:
        return JsonResponse(data)

    for government in results:

        item = {
            'government_id': government.id,
            'government_name': government.name,
            'contributions': None,
            'contributions_year': None,
            'liabilities': None,
            'liabilities_year': None
        }

        contributions = PensionMapData.get_contributions(government.id, request.GET.get('year'))
        liabilities = PensionMapData.get_liabilities(government.id, request.GET.get('year'))

        if contributions:
            item['contributions'] = contributions.plan_contributions
            item['contributions_year'] = contributions.year

        if liabilities:
            item['liabilities'] = liabilities.plan_liabilities
            item['liabilities_year'] = liabilities.year

        data['governments'].append(item)

    return JsonResponse(data)

def api_map_contribs(request, state):
    from django.forms.models import model_to_dict

    data = {'contributions': [], 'success': True}

    results = PensionMapData.get_contributions_by_state(state, request.GET.get('year'))
    fields = ['government_id', 'government_name', 'year', 'plan_name', 'plan_contributions']
    data['contributions'] = [model_to_dict(result, fields) for result in results]

    return JsonResponse(data)


def api_map_liabilities(request, state):
    from django.forms.models import model_to_dict

    data = {'liabilities': [], 'success': True}

    results = PensionMapData.get_liabilities_by_state(state, request.GET.get('year'))
    fields = ['government_id', 'government_name', 'year', 'plan_name', 'plan_liabilities']
    data['liabilities'] = [model_to_dict(result, fields) for result in results]

    return JsonResponse(data)

def api_chart_contribs(request, government_id):

    data = {'headers': {'f1': '', 'f2': ''}, 'values': [], 'success': True}

    rows = PensionChartData.get(government_id)

    if rows == []:
        return JsonResponse(data)

    data['headers']['f1'] = rows[0].f1_header
    data['headers']['f2'] = rows[0].f2_header

    for row in  PensionChartData.get(government_id):
        data['values'].append({
            'year': row.year,
            'f1': row.f1_value,
            'f2': row.f2_value
        })

    return JsonResponse(data)


@staff_member_required
def plan_calculated_status(request):
    plan_attribute_id = request.GET.get('plan_attribute_id')
    plan_attribute = PlanAttribute.objects.get(id=plan_attribute_id)
    status = plan_attribute.status_calculated
    name = plan_attribute.name
    return JsonResponse({
        'result': 'success',
        'plan_attribute_id': plan_attribute_id,
        'status': status,
        'name': name
    })

@staff_member_required
def get_calculated_task_status(request):
    task_id = request.GET.get('task_id')
    current_task = AsyncResult(task_id)
    return JsonResponse({
        "result": current_task.result or current_task.status
    })

@staff_member_required
def generate_reporting_table(request):
    if request.POST:
        task_reporting_table.delay()
    return redirect('/admin/pensiondata/reportingtable/')

# NOTE:  This part should be changed/optimized to Class based View later
@staff_member_required
def delete_plan_annual_attr(request):
    attr_id = request.POST.get('attr_id')
    try:
        obj = PlanAnnualAttribute.objects.get(id=attr_id)
        obj.delete()
        moderation.pre_delete_handler(sender=PlanAnnualAttribute, instance=obj)

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
        # post_save.disconnect(recalculate, sender=PlanAnnualAttribute)
        # moderation.pre_save_handler(sender=PlanAnnualAttribute, instance=obj)
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

        # disconnect signal because of moderation
        post_save.disconnect(recalculate, sender=PlanAnnualAttribute)
        moderation.pre_save_handler(sender=PlanAnnualAttribute, instance=new_plan_annual_attr_obj)
        new_plan_annual_attr_obj.save()
        moderation.post_save_handler(
            sender=PlanAnnualAttribute, instance=new_plan_annual_attr_obj, created=True, view_able=True)
        post_save.connect(recalculate, sender=PlanAnnualAttribute)

        automoderate(new_plan_annual_attr_obj, request.user)

        return JsonResponse({'result': 'success', 'id': new_plan_annual_attr_obj.id})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'result': 'fail', 'msg': 'Something went wrong.'})


@staff_member_required
def delete_gov_annual_attr(request):
    attr_id = request.POST.get('attr_id')
    try:
        obj = GovernmentAnnualAttribute.objects.get(id=attr_id)
        obj.delete()
        moderation.pre_delete_handler(sender=GovernmentAnnualAttribute, instance=obj)


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

        # disconnect signal becuase of moderation
        post_save.disconnect(recalculate, sender=GovernmentAnnualAttribute)
        moderation.pre_save_handler(sender=GovernmentAnnualAttribute, instance=obj)
        obj.save()
        moderation.post_save_handler(sender=GovernmentAnnualAttribute, instance=obj, created=False)
        post_save.connect(recalculate, sender=GovernmentAnnualAttribute)

        automoderate(obj, request.user)
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

        except GovernmentAnnualAttribute.DoesNotExist:
            pass
        except GovernmentAnnualAttribute.MultipleObjectsReturned:
            return JsonResponse({'result': 'fail', 'msg': 'Already exists.'})

        new_gov_annual_attr_obj = GovernmentAnnualAttribute(
            government=gov_obj,
            year=year,
            government_attribute=gov_attr_obj,
            attribute_value=value,
            is_from_source=is_from_source
        )

        # disconnect signal becuase of moderation
        post_save.disconnect(recalculate, sender=PlanAnnualAttribute)
        moderation.pre_save_handler(sender=PlanAnnualAttribute, instance=new_gov_annual_attr_obj)
        new_gov_annual_attr_obj.save()
        moderation.post_save_handler(sender=PlanAnnualAttribute, instance=new_gov_annual_attr_obj, created=True)
        post_save.connect(recalculate, sender=PlanAnnualAttribute)

        automoderate(new_gov_annual_attr_obj, request.user)

        return JsonResponse({'result': 'success'})
    except Exception as e:
        return JsonResponse({'result': 'fail', 'msg': 'Something went wrong.'})


def save_checklist(request):
    """
    save column-visiblity status in session.
    """
    try:

        is_admin_page = request.POST.get('is_admin_page', False)

        model_name = request.POST.get('model_name')
        if is_admin_page and request.user.is_superuser:
            session_key = model_name + '_column_state_admin'
            request.session[session_key] = {'category': [], 'source': [], 'attr': []}
        else:
            session_key = model_name + '_column_state'
        # request.session[session_key] = {'category': [], 'source': [], 'attr': []}
        checked_dict = request.session[session_key]
        checked_dict['category'] = list(map(int, request.POST.getlist('category_checked_states[]')))
        checked_dict['source'] = list(map(int, request.POST.getlist('datasource_checked_states[]')))
        checked_dict['attr'] = list(map(int, request.POST.getlist('attr_checked_states[]')))

        return JsonResponse({'result': 'success'})
    except Exception as e:
        return JsonResponse({'result': 'fail', 'msg': 'Something went wrong.'})


# Added by Marc - 2017-12-19
def export_file(request):
        year_from = request.GET.get('from', '')
        year_to = request.GET.get('to', '')

        file_type, plan_id = request.GET['file_type'], request.GET['plan_id']
        order_columns = []
        if request.GET.get('order_columns'):
            order_columns = [int(v) for v in request.GET.get('order_columns').split(',') or []]

        # Get Date Stamp for the File Name
        now = time.strftime("%Y-%m-%d")

        # Get Plan Display Name for the File Name
        plan_display_name = Plan.objects.get(id=plan_id).display_name

        # Get columns names
        order_col_names = []
        if order_columns:
            order_col = list(PlanAttribute.objects.filter(id__in=order_columns).values_list(
                'id', 'attribute_column_name'
            ))
            order_col.sort(key=lambda x: order_columns.index(int(x[0])))
            order_col_names = list(i[1] for i in order_col)

        # Get Plan Attributes for the Specified Plan and Store in a DataFrame
        query = PlanAnnualAttribute.objects.filter(plan=plan_id, year__range=(year_from or '1950', year_to or '2050'))
        # Include to file only specified fields if required
        if request.GET.get('fields', 'all') == 'selected':
            query = query.filter(
                plan_attribute__id__in=request.session.get('plan_column_state', {}).get('attr', [])
            )
        elif request.GET.get('fields') not in ('all', 'selected'):
            pr_export = list(PresentationExport.objects.filter(export_group__name=request.GET.get('fields')))
            plan_attr_ids = []
            if pr_export:
                pr_export.sort(key=lambda x: x.order)
                plan_attr_ids = [i.plan_field.id for i in pr_export]
                order_col_names = [i.plan_field.attribute_column_name for i in pr_export]
            query = query.filter(
                plan_attribute__id__in=plan_attr_ids
            )

        data = list(query.values_list('year', 'plan_attribute__attribute_column_name', 'attribute_value'))

        # Fix duplicate keys
        for index, item in enumerate(data):
            try:
                if item[1] in ('year'):
                    new_tp = tuple([item[0], u'year_1', item[2]])
                    data[index] = new_tp
            except Exception as e:
                traceback.print_exc()

        df = pandas.DataFrame(data, columns=['year', 'attribute_column_name', 'attribute_value'])

        # Create pivot table
        pivoted = df.pivot(index='year', columns='attribute_column_name', values='attribute_value')

        # Change order of columns if required
        if order_col_names and len(pivoted.columns) == len(order_col_names):
            pivoted = pivoted.reindex(order_col_names, axis=1)

        if file_type == "csv":
            # Output DataFrame to CSV
            file_name = plan_display_name + ' ' + now + '.csv'
            pivoted.to_csv(path_or_buf = file_name)
            file_like = open(file_name, "rb")
            wrapper = FileWrapper(file_like)
            response = HttpResponse(wrapper, content_type='application/csv')
            response['Content-Disposition'] = 'attachment; filename=%s' % file_name.replace(',', '')

        elif file_type == "json":
            # Output DataFrame to JSON
            file_name = plan_display_name + ' ' + now + '.json'
            pivoted.to_json(path_or_buf = file_name)
            file_like = open(file_name, "rb")
            wrapper = FileWrapper(file_like)
            response = HttpResponse(wrapper, content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename=%s' % file_name.replace(',', '')

        elif file_type == "stata":
            # Convert values to string, because 'stata' can't use some formats
            for colname in list(pivoted.select_dtypes(include=['object']).columns):
                try:
                    pivoted[colname] = pivoted[colname].astype('str')
                except Exception as e:
                    traceback.print_exc()

            # Output DataFrame to Stata
            file_name = plan_display_name + ' ' + now + '.dta'
            pivoted.to_stata(fname=file_name)
            file_like = open(file_name, "rb")
            wrapper = FileWrapper(file_like)
            response = HttpResponse(wrapper, content_type='application/stata')
            response['Content-Disposition'] = 'attachment; filename=%s' % file_name.replace(',', '')

        elif file_type == "xlsx":
            # Output DataFrame to XSLX
            writer = pandas.ExcelWriter(
                plan_display_name + ' ' + now + '.xlsx',
                engine='xlsxwriter',
                options={'strings_to_numbers': True}
            )
            file_name = plan_display_name + ' ' + now + '.xlsx'
            pivoted.to_excel(writer, sheet_name='Sheet1')
            writer.save()
            file_like = open(file_name, "rb")
            wrapper = FileWrapper(file_like)
            response = HttpResponse(wrapper, content_type='application/ms-excel')
            response['Content-Disposition'] = 'attachment; filename=%s' % file_name.replace(',', '')

        return response

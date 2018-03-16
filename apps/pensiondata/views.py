from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView, DetailView
from django.views.generic.list import ListView
from django_tables2 import RequestConfig
from django.shortcuts import get_object_or_404, redirect
from django.db import connection
from django.db.utils import  ProgrammingError
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from django.db.models import F, Case, When, Value, BooleanField
import json
import os
import psycopg2
import traceback
import csv
import sys
import time
import pandas
from wsgiref.util import FileWrapper
from celery.result import AsyncResult

from .models import Plan, PlanAnnualAttribute, AttributeCategory, PlanAttribute, DataSource, PlanAnnual, \
                    Government, GovernmentAnnualAttribute, GovernmentAttribute, PresentationExport, ExportGroup
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

    def get_context_data(self, **kwargs):

        year_from = self.request.POST.get('from', '')
        year_to = self.request.POST.get('to', '2021')

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

        # getting columns from the POST request
        if self.request.method == 'POST':
            print ("This is a POST request")
            selected_attr_list = self.request.POST.getlist('attr_checked_states[]')
        # getting columns from session
        elif (self.request.session.get('plan_column_state')):
            selected_attr_list = self.request.session['plan_column_state']['attr']
        # using default columns if got nothing from POST request or saved session
        else:
            selected_attr_list = [CONTRIB_STATE_EMPL,  \
                                 CONTRIB_LOCAL_EMPL,  \
                                 CONTRIB_LOCAL_GOVT,  \
                                 TOTAL_CONTRIB_STATE, \
                                 TOT_BEN_PAYM,        \
                                 ADMIN_EXP,           \
                                 TOT_CASH_SEC,        \
                                 TOT_ACT_MEM]

        plan_annual_objs = PlanAnnualAttribute.objects \
            .select_related('plan_attribute') \
            .select_related('plan_attribute__attribute_category') \
            .select_related('plan_attribute__data_source') \
            .filter(plan=plan)

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
    print('!!!!!!!')
    if request.POST:
        print("POST-----")
        # drop table if exists
        with connection.cursor() as cursor:
            # drop table if exists
            cursor.execute('DROP TABLE IF EXISTS reporting_table')
            # create start part of table
            cursor.execute('''

            CREATE TABLE reporting_table (
            id bigserial primary key,
            plan_id bigint,
            census_plan_id varchar(255),
            name   varchar(255),
            display_name      varchar(255),             
            year_of_inception   int,            
            benefit_tier int,         
            year_closed  int,                 
            web_site  varchar(255),
            soc_sec_coverage boolean,
            soc_sec_coverage_notes  varchar(255),
             includes_state_employees boolean,
             includes_local_employees boolean,
             includes_safety_employees boolean,
             includes_general_employees boolean,
             includes_teachers boolean,
             intra_period_data_entity_id bigint, 
             intra_period_data_period_end_date date,
             intra_period_data_period_type int,
             gasb_68_type varchar(255),
             state_gov_role varchar(255),
             notes text,
             system_assigned_employer_id varchar(255),
             latitude NUMERIC,
             longitude NUMERIC,
             year varchar(255),
             admin_gov_id bigint,
             employ_gov_id bigint
            );
            ''')

            # add column to table reporting_table from every instanse of Plan Attribute
            i = 0
            for plan_attr in PlanAttribute.objects.all():
                try:
                    if plan_attr.attribute_column_name is None or plan_attr.attribute_column_name == 'id' \
                            or " " in plan_attr.attribute_column_name:
                        pass
                    else:
                        add_col_str = 'ALTER TABLE reporting_table ADD COLUMN {} varchar(255);'.format(
                            str(plan_attr.attribute_column_name))
                    cursor.execute(add_col_str)
                # cannot add columns with current name
                except ProgrammingError:
                    pass

            scope_all_plan_an_attr = PlanAnnualAttribute.objects.select_related('plan', 'plan_attribute')

            def check_none(attr):
                if not attr:
                    return "NULL"
                else:
                    return attr

            def check_boolean_none(attr):
                if attr is None:
                    return "NULL"
                else:
                    return "'%s'"%(attr)

            i = 0
            for plan in Plan.objects.filter(id__lte=1):
                scope_for_current_plan = PlanAnnualAttribute.objects.select_related('plan', 'plan_attribute').filter(plan=plan)
                print(scope_for_current_plan.count())
                print(plan.id)
                for current_plan in scope_for_current_plan:

                    # current_plan.plan.
                    str_insert = '''
                    INSERT INTO reporting_table
                    ( plan_id, census_plan_id )
                    VALUES ( {plan_id} , {census_plan_id}, {display_name} )
                    '''.format(
                        plan_id=current_plan.plan.id,
                        census_plan_id=check_none(current_plan.plan.census_plan_id),
                        display_name=check_none(current_plan.plan.display_name.replace("'", "").replace('"', '')),
                        # year_of_inception=check_none(current_plan.plan.year_of_inception)
                    )
                    print(current_plan.plan.display_name.replace("'", "").replace('"', ''))


                    # str_insert = '''
                    # INSERT INTO reporting_table
                    # ( id , census_plan_id ,name , display_name, year_of_inception, benefit_tier, year_closed, web_site, soc_sec_coverage,
                    # soc_sec_coverage_notes, includes_state_employees, includes_local_employees, includes_safety_employees,
                    # includes_general_employees, includes_teachers, intra_period_data_entity_id, intra_period_data_period_end_date,
                    # intra_period_data_period_type, gasb_68_type, state_gov_role, notes, system_assigned_employer_id, latitude, longitude,
                    # year, admin_gov_id, employ_gov_id, plan_id )
                    # VALUES ( {id} , '{census_plan_id}' , '{name}' , '{display_name}', {year_of_inception}, {benefit_tier}, {year_closed}, '{web_site}', {soc_sec_coverage},
                    # '{soc_sec_coverage_notes}', {includes_state_employees}, {includes_local_employees}, {includes_safety_employees},
                    # {includes_general_employees}, {includes_teachers}, '{intra_period_data_entity_id}', '{intra_period_data_period_end_date}',
                    # '{intra_period_data_period_type}', '{gasb_68_type}', '{state_gov_role}', '{notes}', '{system_assigned_employer_id}', '{latitude}', '{longitude}',
                    # '{year}', '{admin_gov_id}', '{employ_gov_id}', '{plan_id}' )
                    # '''.format(
                    #     id=current_plan.plan.id,
                    #     census_plan_id=current_plan.plan.census_plan_id,
                    #     name=current_plan.plan.name,
                    #     display_name=current_plan.plan.display_name.replace("'", "").replace('"', ''),
                    #     year_of_inception=check_none(current_plan.plan.year_of_inception),
                    #     benefit_tier=check_none(current_plan.plan.benefit_tier),
                    #     year_closed=check_none(current_plan.plan.year_closed),
                    #     web_site=check_none(current_plan.plan.web_site),
                    #     soc_sec_coverage=check_boolean_none(current_plan.plan.soc_sec_coverage),
                    #     soc_sec_coverage_notes=current_plan.plan.soc_sec_coverage_notes,
                    #     includes_state_employees=check_boolean_none(current_plan.plan.includes_state_employees),
                    #     includes_local_employees=check_boolean_none(current_plan.plan.includes_local_employees),
                    #     includes_safety_employees=check_boolean_none(current_plan.plan.includes_safety_employees),
                    #     includes_general_employees=check_boolean_none(current_plan.plan.includes_general_employees),
                    #     includes_teachers=check_boolean_none(current_plan.plan.includes_teachers),
                    #     intra_period_data_entity_id=check_none(current_plan.plan.intra_period_data_entity_id),
                    #     intra_period_data_period_end_date=check_none(current_plan.plan.intra_period_data_period_end_date),
                    #     intra_period_data_period_type=check_none(current_plan.plan.intra_period_data_period_type),
                    #     gasb_68_type=check_none(current_plan.plan.gasb_68_type),
                    #     state_gov_role=check_none(current_plan.plan.state_gov_role),
                    #     notes=check_none(current_plan.plan.notes),
                    #     system_assigned_employer_id=current_plan.plan.system_assigned_employer_id,
                    #     latitude=current_plan.plan.latitude,
                    #     longitude=current_plan.plan.longitude,
                    #     year=current_plan.year,
                    #     admin_gov_id=current_plan.plan.admin_gov_id,
                    #     employ_gov_id=current_plan.plan.employ_gov_id,
                    #     plan_id=current_plan.plan_id
                    # )

                    cursor.execute(str_insert)
                    # exist_str =
                #     if i == 10000:
                #         break
                #     i += 1
                # if i == 10000:
                #     break

                #print(i)


                # if plan_attr.attribute_column_name is None or plan_attr.attribute_column_name == 'id':
                #     name = plan_attr.name.replace(" ", "_")
                #     add_col_str = 'ALTER TABLE reporting_table ADD COLUMN {} varchar(255);'.format(
                #         str(name))
                # elif " " in  plan_attr.attribute_column_name:
                #     name = plan_attr.name.replace(" ", "_")
                #     add_col_str = 'ALTER TABLE reporting_table ADD COLUMN {} varchar(255);'.format(
                #         str(name))
                # else:
                #     add_col_str = 'ALTER TABLE reporting_table ADD COLUMN {} varchar(255);'.format(str(plan_attr.attribute_column_name))
                #
                # # cannot add columns with current name
                # try:
                #     cursor.execute(add_col_str)
                # except ProgrammingError:
                #     pass
                # if i == 5:
                #     break
                # i += 1
        # i = 0
        # for item in Plan.objects.filter(id__lte=1):
        #     print(item)
        #     scope_for_current_plan = PlanAnnualAttribute.objects.select_related('plan').filter(plan=item)#
        #     print(scope_for_current_plan.count())
            # for it in scope_for_current_plan:
            #     plan = it.plan
            #     print(plan)
            #print(scope_for_current_plan.count())

        # with connection.cursor() as cursor:
        #     cursor.execute('''CREATE TABLE test_bla (id integer);''')

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

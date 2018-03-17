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
            list_all_attribute_column_name = []
            for plan_attr in PlanAttribute.objects.all():
                if plan_attr.attribute_column_name is None or plan_attr.attribute_column_name == 'id' \
                        or " " in plan_attr.attribute_column_name or plan_attr.attribute_column_name == 'plan_id'\
                        or plan_attr.attribute_column_name == 'year':
                    pass
                else:
                    list_all_attribute_column_name.append(str(plan_attr.attribute_column_name))
            # only unique attribute_column_name
            list_all_attribute_column_name = list(set(list_all_attribute_column_name))
            #try:
            for one_attr_col_name in list_all_attribute_column_name:
                print(one_attr_col_name)
                cursor.execute('ALTER TABLE reporting_table ADD COLUMN {} varchar(255);'.format(str(one_attr_col_name)))
            #except ProgrammingError:
            #   list_all_attribute_column_name.remove(one_attr_col_name)


                # try:
                #     if plan_attr.attribute_column_name is None or plan_attr.attribute_column_name == 'id' \
                #             or " " in plan_attr.attribute_column_name:
                #         pass
                #     else:
                #         add_col_str = 'ALTER TABLE reporting_table ADD COLUMN {} varchar(255);'.format(
                #             str(plan_attr.attribute_column_name))
                #         list_all_attribute_column_name.append(str(plan_attr.attribute_column_name))
                #     cursor.execute(add_col_str)
                # # cannot add columns with current name
                # except ProgrammingError:
                #     pass

            scope_all_plan_an_attr = PlanAnnualAttribute.objects.select_related('plan', 'plan_attribute')

        def check_none(attr):
            if not attr:
                return "NULL"
            else:
                return attr

        def convet_none_to_null(attr):
            if not attr:
                return "NULL"
            else:
                return attr

        def check_boolean_none(attr):
            if attr is None:
                return "NULL"
            else:
                return "'%s'"%(attr)


        print(len(list(set(list_all_attribute_column_name))))
        print(list(set(list_all_attribute_column_name)))

        i = 0
        for plan in Plan.objects.filter(id__lte=1):
            scope_for_current_plan = PlanAnnualAttribute.objects.select_related('plan', 'plan_attribute').filter(plan=plan)
            print(scope_for_current_plan.count())

            qs_years = scope_for_current_plan.values_list('year', flat=True)
            current_plan = scope_for_current_plan.first().plan
            qs_plan_attribute_id = scope_for_current_plan.values_list('plan_attribute_id', flat=True)
            dict_plan_attr_and_attr_value = {}
            t = 0
            # for item in list_all_attribute_column_name:
            #     if item in qs_plan_attribute_id:
            #         qs_plan_attribute_id
            #         t += 1
            # print("===  t ",t )
            # for item in list_all_attribute_column_name:
            #     cur_id = PlanAttribute.objects.filter(attribute_column_name=item)[0].id
            #     print(cur_id)
            # for pl_attr in qs_plan_attribute_id:
            #     print(pl_attr)


            print(qs_plan_attribute_id)
            print(len(qs_plan_attribute_id))
            print(current_plan)

            dict_plan_attr_and_attr_value_with_years = {}
            for y in qs_years:
                dict_plan_attr_and_attr_value_with_years[y]={}

            pprint(dict_plan_attr_and_attr_value_with_years)
            # for curr_year in qs_years:
            #     for item in list_all_attribute_column_name:
            #         cur_id = PlanAttribute.objects.filter(attribute_column_name=item)[0].id
            #         case_exist = scope_for_current_plan.filter(year=curr_year, plan_attribute_id=cur_id)
            #         if case_exist.exists() :
            #             # dict_plan_attr_and_attr_value[item] = convet_none_to_null(case_exist[0].attribute_value)
            #             dict_plan_attr_and_attr_value_with_years[curr_year] [item] = convet_none_to_null(case_exist[0].attribute_value)
            #             # dict_plan_attr_and_attr_value_with_years[curr_year][item] = convet_none_to_null(case_exist[0].attribute_value)
            #     #dict_plan_attr_and_attr_value_with_years[curr_year] = dict_plan_attr_and_attr_value
            #
            #             #dict_plan_attr_and_attr_value[item]=case_exist[0].attribute_value
            #             #print(item, "======", case_exist[0].attribute_value,"======" ,type(case_exist[0].attribute_value))
            # pprint(dict_plan_attr_and_attr_value_with_years)

            dict_2016 = {'actassets_ava': 'NULL',
                 'actassets_est': '0',
                 'actassets_gasb': 'NULL',
                 'actassets_smooth': 'NULL',
                 'actcostmeth': 'NULL',
                 'actcostmeth_gasb': 'Entry Age Normal',
                 'actcostmeth_note': 'NULL',
                 'actcostmethcode': 'NULL',
                 'actcostmethcode_gasb': '1',
                 'actfundedratio_est': '0',
                 'actfundedratio_gasb': 'NULL',
                 'actfundedratio_gasb67': 'NULL',
                 'activeage_avg': 'NULL',
                 'actives_tot': 'NULL',
                 'activesalaries': 'NULL',
                 'activesalary_avg': 'NULL',
                 'activesalary_avg_est': '0',
                 'activetenure_avg': 'NULL',
                 'actliabilities_ean': 'NULL',
                 'actliabilities_est': '0',
                 'actliabilities_gasb': 'NULL',
                 'actliabilities_other': '0',
                 'actliabilities_puc': 'NULL',
                 'actrpt_cy': 'NULL',
                 'actrptdate': 'NULL',
                 'actuarially_accured_liabilities': '15723720',
                 'actvaldate_actuarialcosts': 'NULL',
                 'actvaldate_gasbschedules': 'NULL',
                 'addsubtractgainloss': 'NULL',
                 'adec': 'NULL',
                 'adjustment_mktassets': 'NULL',
                 'administeringgovt': '0',
                 'administrative_expenses': '13885',
                 'aec': 'NULL',
                 'all_other_short_term_investments': '300574',
                 'alternatives': '0',
                 'arc': 'NULL',
                 'assetsmoothingbaseline': 'NULL',
                 'assetsmoothingperiod_gasb': '5',
                 'assetvalmeth': 'NULL',
                 'assetvalmeth_gasb': '5-year smoothed market ',
                 'assetvalmeth_note': 'NULL',
                 'assetvalmethcode': 'NULL',
                 'assetvalmethcode_gasb': '0',
                 'beneficiaries_dependentsurvivors': 'NULL',
                 'beneficiaries_disabilityretirees': 'NULL',
                 'beneficiaries_other': 'NULL',
                 'beneficiaries_serviceretirees': 'NULL',
                 'beneficiaries_spousalsurvivors': 'NULL',
                 'beneficiaries_survivors': 'NULL',
                 'beneficiaries_tot': 'NULL',
                 'beneficiaryage_avg': 'NULL',
                 'beneficiarybenefit_avg': 'NULL',
                 'beneficiarybenefit_avg_est': '0',
                 'benefits_disabilityretirees': 'NULL',
                 'benefits_serviceretirees': 'NULL',
                 'benefits_tot': 'NULL',
                 'benefitswebsite': 'http',
                 'blendeddiscountrate': '0.0775000005960464478',
                 'cafr_av_conflict': 'NULL',
                 'cafr_cy': 'NULL',
                 'cash_on_hand_and_demand_deposits': '186433',
                 'cashandshortterm': '0',
                 'cola_code': 'NULL',
                 'cola_verabatim': 'NULL',
                 'contrib_ee_other': 'NULL',
                 'contrib_ee_purchaseservice': 'NULL',
                 'contrib_ee_regular': '231794',
                 'contrib_er_other': 'NULL',
                 'contrib_er_regular': '435098',
                 'contrib_er_state': 'NULL',
                 'contrib_other': '6223',
                 'contrib_tot': '673115',
                 'contributionfy': 'NULL',
                 'contributions_by_local_employees': '77689',
                 'contributions_by_state_employees': '154105',
                 'corporate_bonds_other': '2316304',
                 'corporate_stocks': '5850539',
                 'costsharing': '0',
                 'coststructure': 'Multiple employer, agent plan',
                 'covered_payroll': '3488017',
                 'coveredpayroll_gasb67': 'NULL',
                 'coverslocalemployees': '1',
                 'coversstateemployees': '1',
                 'coversteachers': '0',
                 'dataentrycode': 'NULL',
                 'disability_benefits': '57661',
                 'dividend_earnings': '0',
                 'dropmembers': 'NULL',
                 'eegroupid': '0',
                 'electedofficials': '0',
                 'employeetypecovered': 'Plan covers state and local employees',
                 'employertype': '2',
                 'equities_domestic': '0.529799997806549072',
                 'equities_international': '0.114100001752376556',
                 'equities_tot': '0.643899977207183838',
                 'expectedreturnmethod': 'NULL',
                 'expense_adminexpenses': '-11002',
                 'expense_alternatives': 'NULL',
                 'expense_colabenefits': 'NULL',
                 'expense_deathbenefits': 'NULL',
                 'expense_depreciation': '-2021',
                 'expense_disabilitybenefits': 'NULL',
                 'expense_dropbenefits': 'NULL',
                 'expense_investments': '-2883',
                 'expense_lumpsumbenefits': 'NULL',
                 'expense_net': '-1100976',
                 'expense_otherbenefits': '-45768',
                 'expense_otherdeductions': '-3668',
                 'expense_otherinvestments': 'NULL',
                 'expense_privateequity': 'NULL',
                 'expense_realestate': 'NULL',
                 'expense_refunds': 'NULL',
                 'expense_retbenefits': '-1038517',
                 'expense_seclendmgmtfees': '-1416',
                 'expense_securitieslending': '-2772',
                 'expense_survivorbenefits': 'NULL',
                 'expense_totbenefits': '-1084285',
                 'fairvaluechange_investments': '753836',
                 'fairvaluechange_realestate': 'NULL',
                 'fairvaluechange_seclend': 'NULL',
                 'fairvaluechange_seclendug': 'NULL',
                 'federal_agency_securities': '0',
                 'federal_treasury_securities': '0',
                 'federally_sponsored_agencies': '0',
                 'fiscalyeartype': '1',
                 'fixedincome_domestic': '0.155699998140335083',
                 'fixedincome_international': '0',
                 'fixedincome_tot': '0.253800004720687866',
                 'foreign_and_international_securities': '1260074',
                 'former_active_members_retired_on_account_of_disability': '4120',
                 'fundingmeth': 'NULL',
                 'fundingmeth_gasb': 'Level Percent Closed',
                 'fundingmeth_note': 'NULL',
                 'fundingmethcode1_gasb': '1',
                 'fundingmethcode2_gasb': '3',
                 'fundmethcode_1': 'NULL',
                 'fundmethcode_2': 'NULL',
                 'fy': '2016',
                 'fye': '2016-09-30',
                 'gainloss': 'NULL',
                 'gainlossbase_1': 'NULL',
                 'gainlossbase_2': 'NULL',
                 'gainlossconcept': 'NULL',
                 'gainlossperiod': 'NULL',
                 'gainlossrecognition': 'NULL',
                 'geogrowth_est': '0.0220383889973163605',
                 'georeturn_est': '0.050627436488866806',
                 'govtname': 'Alabama',
                 'grossreturns': '0',
                 'inactive_members': '9641',
                 'inactivenonvested': 'NULL',
                 'inactivevestedmembers': 'NULL',
                 'income_alternatives': 'NULL',
                 'income_dividends': 'NULL',
                 'income_interest': 'NULL',
                 'income_interestanddividends': '297369',
                 'income_international': 'NULL',
                 'income_net': '1726146',
                 'income_otheradditions': 'NULL',
                 'income_otherinvestments': 'NULL',
                 'income_privateequity': 'NULL',
                 'income_realestate': 'NULL',
                 'income_securitieslending': '7481',
                 'income_securitieslendingrebate': '-1356',
                 'inflationassumption_gasb': '0.0299999993294477463',
                 'inpfs': '1',
                 'interest_earnings': '297369',
                 'investmentreturn_10yr': '0.0534000024199485779',
                 'investmentreturn_10yr_est': '0',
                 'investmentreturn_12yr': 'NULL',
                 'investmentreturn_15yr': 'NULL',
                 'investmentreturn_1yr': '0.10220000147819519',
                 'investmentreturn_1yr_est': '0',
                 'investmentreturn_20yr': 'NULL',
                 'investmentreturn_25yr': 'NULL',
                 'investmentreturn_2yr': 'NULL',
                 'investmentreturn_30yr': 'NULL',
                 'investmentreturn_3yr': '0.0764999985694885254',
                 'investmentreturn_4yr': 'NULL',
                 'investmentreturn_5yr': '0.11029999703168869',
                 'investmentreturn_5yr_est': '0',
                 'investmentreturn_7yr': 'NULL',
                 'investmentreturn_8yr': 'NULL',
                 'investmentreturn_longterm': 'NULL',
                 'investmentreturn_longtermstartye': 'NULL',
                 'investmentreturnassumption_gasb': '0.0799999982118606567',
                 'investments_held_in_trust_by_other_agencies': '0',
                 'judgesattorneys': '0',
                 'local_government_active_members': '54627',
                 'local_government_contributions': '257602',
                 'localemployers': '1',
                 'localfire': '0',
                 'localgenee': '1',
                 'localpolice': '0',
                 'losses_on_investments': '0',
                 'lowercorridor': 'NULL',
                 'members_retired_on_account_of_age_or_service': '38247',
                 'mktassets_actrpt': 'NULL',
                 'mktassets_net': '11177074',
                 'mktassets_smooth': 'NULL',
                 'mortgages_held_directly': '0',
                 'net_gains_on_investments': '753836',
                 'netflows_smooth': 'NULL',
                 'netpensionliability': 'NULL',
                 'netposition': 'NULL',
                 'noav': 'NULL',
                 'nocafr': 'NULL',
                 'normcostamount_ee': 'NULL',
                 'normcostamount_er': 'NULL',
                 'normcostamount_tot': 'NULL',
                 'normcostrate_ee': 'NULL',
                 'normcostrate_ee_est': '0',
                 'normcostrate_er': 'NULL',
                 'normcostrate_er_est': '0',
                 'normcostrate_tot': 'NULL',
                 'normcostrate_tot_est': '0',
                 'other': '0',
                 'other_benefits': '0',
                 'other_investment_earnings': '4709',
                 'other_investments': '0',
                 'other_securities': '0',
                 'othermembers': 'NULL',
                 'payroll': 'NULL',
                 'payrollgrowthassumption': 'NULL',
                 'percentadec': 'NULL',
                 'percentarcpaid': 'NULL',
                 'percentreqcontpaid': 'NULL',
                 'phasein': 'NULL',
                 'phaseinpercent': 'NULL',
                 'phaseinperiods': 'NULL',
                 'phaseintype': 'NULL',
                 'plan_annual_id': '1177068',
                 'planclosed': '0',
                 'planfullname': 'Employeesе Retirement System of Alabama',
                 'planinceptionyear': '1945',
                 'planleveldata': '1',
                 'planname': 'Alabama ERS',
                 'plantype': '1',
                 'planyearclosed': 'NULL',
                 'ppd_id': '1',
                 'projectedpayroll': 'NULL',
                 'pvfb_active': 'NULL',
                 'pvfb_inactivenonvested': 'NULL',
                 'pvfb_inactivevested': 'NULL',
                 'pvfb_other': 'NULL',
                 'pvfb_retiree': 'NULL',
                 'pvfb_tot': 'NULL',
                 'pvfnc_ee': 'NULL',
                 'pvfnc_er': 'NULL',
                 'pvfnc_tot': 'NULL',
                 'pvfs': 'NULL',
                 'real_property': '1129763',
                 'realestate': '0.102299995720386505',
                 'remainingamortperiod': 'NULL',
                 'rentals_from_state_government': '0',
                 'reportingdatenotes': 'NULL',
                 'reqcontamount_er': 'NULL',
                 'reqcontamount_tot': 'NULL',
                 'reqcontrate_er': 'NULL',
                 'reqcontrate_er_est': '0',
                 'reqcontrate_tot': 'NULL',
                 'requiredcontribution': 'NULL',
                 'requiredcontribution_est': 'NULL',
                 'retirement_benefits': '937718',
                 'schoolees': '0',
                 'schoolemployers': '0',
                 'serviceretage_avg': 'NULL',
                 'serviceretbenefit_avg': 'NULL',
                 'serviceretireeage_avg': 'NULL',
                 'serviceretireebenefit_avg': 'NULL',
                 'servicerettenure_avg': 'NULL',
                 'smoothingreset': 'NULL',
                 'socseccovered': '1',
                 'socseccovered_verbatim': 'Plan members covered by Social Security',
                 'source_actcosts': 'NULL',
                 'source_actliabilities': 'NULL',
                 'source_assetallocation': '2016 Alabama RS CAFR p 110',
                 'source_fundingandmethods': 'NULL',
                 'source_gasbassumptions': '2016 CAFR p 73',
                 'source_gasbschedules': 'No AV',
                 'source_incomestatement': '2016 CAFR P 28',
                 'source_investmentreturn': '2016 Plan CAFR p 103',
                 'source_membership': 'NULL',
                 'source_planbasics': 'NULL',
                 'state_and_local_government_securities': '0',
                 'state_contributions_on_behalf_of_local_employees': '0',
                 'state_contributions_on_behalf_of_state_employees': '141168',
                 'state_government_active_members': '29936',
                 'stateabbrev': 'AL',
                 'stateemployers': '1',
                 'statefire': '0',
                 'stategenee': '1',
                 'statename': 'Alabama',
                 'statepolice': '1',
                 'survivor_benefits': '43138',
                 'survivors': '3751',
                 'system_id': '1',
                 'teacher': '0',
                 'tierid': '0',
                 'time_or_savings_deposits': '223',
                 'total_active_members': '84563',
                 'total_benefit_payments': '1038517',
                 'total_cash_and_securities': '11043910',
                 'total_cash_and_short_term_investments': '487230',
                 'total_corporate_bonds': '2316304',
                 'total_earnings_on_investments': '1055914',
                 'total_employee_contributions': '231794',
                 'total_federal_government_securities': '0',
                 'total_other_investments': '1129763',
                 'total_other_securities': '1260074',
                 'total_state_contributions': '141168',
                 'totalpensionliability': 'NULL',
                 'totamortperiod': 'NULL',
                 'totmembership': 'NULL',
                 'uaal_gasb': 'NULL',
                 'uaalamortperiod_gasb': '29.8999996185302734',
                 'uaalrate': 'NULL',
                 'uaalyearestablished': 'NULL',
                 'uppercorridor': 'NULL',
                 'valuationid': '1',
                 'wageinflation': 'NULL',
                 'withdrawals': '49436'}

            def my_str(attr):
                if " " in attr:
                    return "'%s'"%(str(attr))
                return attr

            list_keys = list(dict_2016.keys())
            list_values = list(dict_2016.values())
            print(len(list_keys))
            print(len(list_values))
            str_keys = ', '.join(map(str, list_keys))
            str_values = ', '.join(map(my_str, list_values))
            print(str_keys)
            print(str_values)

            with connection.cursor() as cursor:
                for one_year in qs_years:
                    str_insert = '''
                    INSERT INTO reporting_table
                    (plan_id, year, {str_keys})
                    VALUES ({plan_id}, {one_year}, {str_values} )
                    '''.format(
                        str_keys=str_keys,
                        plan_id=current_plan.id,
                        one_year=one_year,
                        str_values=str_values,
                        actassets_ava='NULL',
                        actassets_est='0',
                        actassets_gasb='NULL'

                    )
                    print(str_insert)
                    # for item in list_all_attribute_column_name:
                    #     cur_id = PlanAttribute.objects.filter(attribute_column_name=item)[0].id
                    #     case_exist = scope_for_current_plan.filter(year=one_year, plan_attribute_id=cur_id)
                    #     if case_exist.exists():
                    #         print(cur_id, "======" ,case_exist[0].attribute_value)
                    cursor.execute(str_insert)



                # print(plan.id)
                # for current_plan in scope_for_current_plan:
                #
                #     # current_plan.plan.
                #     str_insert = '''
                #     INSERT INTO reporting_table
                #     ( plan_id, census_plan_id )
                #     VALUES ( {plan_id} , {census_plan_id})
                #     '''.format(
                #         plan_id=current_plan.plan.id,
                #         census_plan_id=check_none(current_plan.plan.census_plan_id),
                #         display_name=check_none(current_plan.plan.display_name.replace("'", "").replace('"', '')),
                #         # year_of_inception=check_none(current_plan.plan.year_of_inception)
                #     )
                #     print(current_plan.plan.display_name.replace("'", "").replace('"', ''))


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

                    # cursor.execute(str_insert)
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

from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView, DetailView
from django.views.generic.list import ListView
from django_tables2 import RequestConfig
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from django.db.models import F, Case, When, Value, BooleanField
import json
import os
import psycopg2
import csv
import sys
import time
import pandas
from wsgiref.util import FileWrapper

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

        # constants for default attribute IDs that need to be fetched
        CONTRIB_STATE_EMPL = 1
        CONTRIB_LOCAL_EMPL = 2
        CONTRIB_LOCAL_GOVT = 4
        TOTAL_CONTRIB_STATE = 5
        TOT_BEN_PAYM = 16
        ADMIN_EXP = 22
        TOT_CASH_SEC = 42
        TOT_ACT_MEM = 43

        selected_attr_list = []

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

        year_list = plan_annual_objs_filtered_attributes.order_by('year').values('year').distinct()

        plan_annual_data = plan_annual_objs_filtered_attributes \
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
            # selected=Q(plan_attribute_id__in=selected_attr_list) # not using Q expression because of a bug in Django with Q and annotate (which seems to be very recently fixed)
            # 'selected' is helpful in checking the options in the checkboxes
            selected=Case(When(plan_attribute_id__in=selected_attr_list, then=Value(True)),default=Value(False),output_field=BooleanField())
        ).distinct().order_by('category_name', 'attribute_name')

        category_list = plan_annual_objs.values(
            'plan_attribute__attribute_category__id',
            'plan_attribute__attribute_category__name'
        ).annotate(
            id=F('plan_attribute__attribute_category__id'),
            name=F('plan_attribute__attribute_category__name'),
            # 'selected' is helpful in checking the options in the checkboxes
            selected=Case(When(plan_attribute_id__in=selected_attr_list, then=Value(True)),default=Value(False),output_field=BooleanField())
        ).distinct().order_by('name','-selected') # -selected is to put True values on top so that later we can remove any False values (which also has True value somewhere)

        category_list=category_list.distinct('name') # this is to remove the selected=False values where selected=True is already there

        # fetching the data source list and marking selected based on selected attribute list
        datasource_list = DataSource.objects.all().annotate( \
            # 'selected' is helpful in checking the options in the checkboxes
            selected=Case(When(id__in=[PlanAttribute.objects.get(id=x).data_source_id for x in selected_attr_list], then=Value(True)),default=Value(False),output_field=BooleanField())
        ).order_by('name')

        # context['attr_list'] = attr_list
        context['full_attr_list'] = full_attr_list
        context['category_list'] = category_list
        context['datasource_list'] = datasource_list
        context['year_list'] = year_list

        context['plan_annual_data'] = json.dumps(list(plan_annual_data))

        return context

    # this is to enable the DetailView to process POST requests (when the user selects different checkboxes than default)
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context=context)

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
        # obj.delete()
        moderation.pre_delete_handler(sender=GovernmentAnnualAttribute, instance=obj)
        moderation.post_delete_handler(sender=GovernmentAnnualAttribute, instance=obj)
        automoderate(obj, request.user)

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

        model_name = request.POST.get('model_name')
        session_key = model_name + '_column_state'

        request.session[session_key] = {'category': [], 'source': [], 'attr': []}
        checked_dict = request.session[session_key]
        checked_dict['category'] = list(map(int, request.POST.getlist('category_checked_states[]')))
        checked_dict['source'] = list(map(int, request.POST.getlist('datasource_checked_states[]')))
        checked_dict['attr'] = list(map(int, request.POST.getlist('attr_checked_states[]')))

        return JsonResponse({'result': 'success'})
    except Exception as e:
        return JsonResponse({'result': 'fail', 'msg': 'Something went wrong.'})


# Added by Marc - 2017-12-19
def export_file(request):
        file_type, plan_id = request.GET['file_type'], request.GET['plan_id']

        #print("In Here")
        #file_type = "csv"
        #plan_id = 222

        # Connection to Azure Postgres Database requires SSH tunneling
        # conn = psycopg2.connect(host="51.141.162.6",database="pension",user="postgres",password="postgres")

        # Connection to Heroku Database
        conn = psycopg2.connect(host="ec2-54-235-177-45.compute-1.amazonaws.com",database="d47an5cjnv5mjb",user="viliygpvlizwel",password="5c26e3ddd0b2682b5c71a4230547677007d7f9fcfe1ed1c29ee45d6375a7475d")

        # Get Date Stamp for the File Name
        now = time.strftime("%Y-%m-%d")

        # Get Plan Display Name for the File Name
        cur = conn.cursor()
        cur.execute("select display_name from plan where id = " + plan_id + ";")
        plan_display_name = cur.fetchone()[0]

        # Get Plan Attributes for the Specified Plan and Store in a DataFrame
        cur.execute("select year, attribute_column_name, attribute_value from plan_annual_attribute inner join plan_attribute on plan_attribute.id = plan_annual_attribute.plan_attribute_id where plan_id = " + plan_id + ";")
        df = pandas.DataFrame(cur.fetchall(), columns=['year','attribute_column_name','attribute_value'])

        # Create pivot table
        pivoted = df.pivot(index='year', columns='attribute_column_name', values='attribute_value')

        if file_type == "csv":

                # Output DataFrame to CSV
                file_name = plan_display_name + ' ' + now + '.csv'
                pivoted.to_csv(path_or_buf = file_name)
                file_like = open(file_name, "rb")
                wrapper = FileWrapper(file_like)
                response = HttpResponse(wrapper, content_type='application/csv')
                response['Content-Disposition'] = 'attachment; filename=%s' % file_name

        elif file_type == "json":

                # Output DataFrame to JSON
                file_name = plan_display_name + ' ' + now + '.json'
                pivoted.to_json(path_or_buf = file_name)
                file_like = open(file_name, "rb")
                wrapper = FileWrapper(file_like)
                response = HttpResponse(wrapper, content_type='application/json')
                response['Content-Disposition'] = 'attachment; filename=%s' % file_name

        elif file_type == "stata":

                # Output DataFrame to Stata
                file_name = plan_display_name + ' ' + now + '.dta'
                pivoted.to_stata(fname = file_name)
                file_like = open(file_name, "rb")
                wrapper = FileWrapper(file_like)
                response = HttpResponse(wrapper, content_type='application/stata')
                response['Content-Disposition'] = 'attachment; filename=%s' % file_name

        elif file_type == "xlsx":

                # Output DataFrame to XSLX
                writer = pandas.ExcelWriter(plan_display_name + ' ' + now + '.xlsx', engine='xlsxwriter', options={'strings_to_numbers': True})
                file_name = plan_display_name + ' ' + now + '.xlsx'
                pivoted.to_excel(writer, sheet_name='Sheet1')
                writer.save()
                file_like = open(file_name, "rb")
                wrapper = FileWrapper(file_like)
                response = HttpResponse(wrapper, content_type='application/ms-excel')
                response['Content-Disposition'] = 'attachment; filename=%s' % file_name


        return response

import re
import os
import time
import datetime
import json

import pandas as pd
import xlrd
from django.db import connection
from django.db.utils import  ProgrammingError
from django.db.utils import  IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task, current_task, task

from .models import PlanAnnualAttribute, PlanAttribute, Plan, DataSource


def parse_calculate_rule_string(qs, attribute_value=False):
    calculated_rule = qs.calculated_rule
    calculated_rule = re.sub('[#]', '', calculated_rule)
    parsed_list = re.findall(r"\%\d+\%|\d+|[\s+-/*]", calculated_rule)

    list_data = []
    list_index_queryset = []

    for item in parsed_list:
        if item.isdigit():
            if not attribute_value:
                plan_annual_attribute = PlanAnnualAttribute.objects.filter(plan_attribute_id=int(item))
            else:
                plan_annual_attribute = PlanAnnualAttribute.objects.filter(
                    plan_attribute_id=int(item), attribute_value=None)
            list_data.append(plan_annual_attribute)
            list_index_queryset.append(parsed_list.index(item))
        else:
            list_data.append(item)

    list_all_parsed_digits = []
    for it in parsed_list:
        for letter in it:
            if any(char.isdigit() for char in letter):
                list_all_parsed_digits.append(it)
    list_all_parsed_digits = list(set(list_all_parsed_digits))

    return list_data, list_index_queryset, parsed_list, list_all_parsed_digits


def get_result_string(parsed_list, list_index_queryset, dict_data, plan, year, qs):
    result_string = ""
    for t in parsed_list:
        if parsed_list.index(t) in list_index_queryset:
            attribute_value = dict_data.get(parsed_list.index(t)).get("attribute_value")
            if not attribute_value:
                attribute_value = ""
                result_string = result_string + attribute_value
            result_string = result_string + attribute_value
        elif "%" in t:
            t = re.findall(r"\d+", t)[0]
            result_string = result_string + t
        else:
            result_string = result_string + t
    return result_string


def parse_list_data(x, qs, list_data, list_index_queryset, parsed_list, list_all_parsed_digits):
    dict_data = {}
    year = x.year
    plan = x.plan
    attribute_value = x.attribute_value
    dict_data[list_index_queryset[0]] = {
        "attribute_value": attribute_value,
        "plan": plan,
        "year": year
    }

    for y in list_index_queryset[1:]:
        for z in list_data[y]:
            if (z.year == year) and (z.plan == plan):
                dict_data[y] = {
                    "attribute_value": z.attribute_value,
                    "plan": z.plan,
                    "year": z.year
                }
        if list(dict_data.keys()) == list_index_queryset:
            result_string = get_result_string(parsed_list, list_index_queryset, dict_data, plan, year, qs)
            total_digits = re.findall('\d+', result_string)
            try:
                result = eval(result_string)
            except SyntaxError:
                result = 0
            if PlanAnnualAttribute.objects.filter(plan=plan, year=year, plan_attribute_id=qs.id).exists():
                new = PlanAnnualAttribute.objects.get(
                    plan=plan, year=year, plan_attribute_id=qs.id)
                new.attribute_value = result
                new.save()
            else:
                PlanAnnualAttribute.objects.get_or_create(
                    plan=plan, year=year, plan_attribute_id=qs.id)


@shared_task
def generate_calculated_fields(list_ids):
    queryset = PlanAttribute.objects.filter(id__in=list_ids)
    for qs in queryset:
        qs.status_calculated = 'in progress'
        qs.save()
        list_data, list_index_queryset, parsed_list, list_all_parsed_digits = parse_calculate_rule_string(qs=qs)
        for x in list_data[list_index_queryset[0]]:
            parse_list_data(x, qs, list_data, list_index_queryset, parsed_list, list_all_parsed_digits)
        qs.status_calculated = "done"
        qs.save()


@shared_task
def generate_calculated_fields_null(list_ids):
    queryset = PlanAttribute.objects.filter(id__in=list_ids)
    for qs in queryset:
        qs.status_calculated = 'in progress'
        qs.save()
        list_data, list_index_queryset, parsed_list, list_all_parsed_digits = parse_calculate_rule_string(
            qs=qs, attribute_value=True)
        for x in list_data[list_index_queryset[0]]:
            parse_list_data(x, qs, list_data, list_index_queryset, parsed_list, list_all_parsed_digits)
        qs.status_calculated = "done"
        qs.save()


@shared_task
def import_to_database(data, model_name, source='Census', format='txt'):
    """
    :param data: list of lines

    """

    current_task.update_state(
                state='PROGRESS',
                meta={'process_percent': 0, 'imported_count': 0}
    )

    row_counts = len(data)
    if row_counts == 0:
        return True

    cur_row_num = 1
    imported_count = 0
    for row in data:
        # NOTE: temporary code. should be optimized.
        if model_name == 'Plan'.lower():
            if import_census_plan(row):
                imported_count += 1
        elif model_name == 'PlanAnnualAttribute'.lower():
            if import_census_plan_annual(row):
                imported_count += 1
        else:
            return 0

        process_percent = int(100 * float(cur_row_num) / float(row_counts))
        current_task.update_state(
            state='PROGRESS',
            meta={'process_percent': process_percent, 'imported_count': imported_count}
        )
        cur_row_num += 1
    return imported_count


def import_census_plan(record):

    # parsing

    try:
        census_plan_id = record[0:14].strip()
        name = record[15:100].strip()
        display_name = record[100:188].strip()

    except Exception as e:
        # print(e.__dict__)
        return False

    # Plan

    try:
        plan_obj = Plan.objects.get(census_plan_id=census_plan_id)
        if not (plan_obj.name == name and plan_obj.display_name == display_name):
            plan_obj.name = name
            plan_obj.display_name = display_name
            plan_obj.save()

    except Plan.DoesNotExist:
        Plan.objects.create(census_plan_id=census_plan_id, name=name, display_name=display_name)

    except Plan.MultipleObjectsReturned:
        # print("NOTE: --- There exists dulplicated census_plan_id in Plan Table --- ")
        return False

    return True


def import_census_plan_annual(record):

    # parsing

    try:
        datasource = DataSource.objects.get(name__exact='Census')  # NOTE: hardcoded
        census_plan_id = record[0:14].strip()
        line_item_code = record[14:17].strip()
        value = record[17:29].strip()
        year = record[31:33]
        if int(year) > 80:
            year = '19' + year
        else:
            year = '20' + year

    except Exception as e:
        # print(e.__dict__)
        return False

    # PlanAttribute

    try:
        plan_attr = PlanAttribute.objects.get(line_item_code=line_item_code, data_source=datasource)
        if plan_attr.name is None:
            plan_attr.name = line_item_code
            plan_attr.save()

    except PlanAttribute.DoesNotExist:
        plan_attr = PlanAttribute.objects.create(name=line_item_code, line_item_code=line_item_code, data_source=datasource)
    except PlanAttribute.MultipleObjectsReturned:
        # print("NOTE: --- There exists dulplicated (line_item_code, data_source) in PlanAttribute Table --- ")
        return False

    # Plan

    try:
        plan_obj = Plan.objects.get(census_plan_id=census_plan_id)
    except Plan.DoesNotExist:
        plan_obj = Plan.objects.create(census_plan_id=census_plan_id, name='undefined plan name')

    except Plan.MultipleObjectsReturned:
        # print("NOTE: --- There exists dulplicated census_plan_id in Plan Table --- ")
        return False

    # PlanAnnualAttribute

    try:
        plan_annual = PlanAnnualAttribute.objects.get(plan=plan_obj, plan_attribute=plan_attr, year=year)
        if not (plan_annual.attribute_value == value):
            plan_annual.attribute_value = value
            plan_annual.save()

    except PlanAnnualAttribute.DoesNotExist:
        PlanAnnualAttribute.objects.create(plan=plan_obj, plan_attribute=plan_attr, year=year, attribute_value=value)

    except PlanAnnualAttribute.MultipleObjectsReturned:
        # print("NOTE: --- There exists dulplicated (planm plan_attribute, year) in PlanAnnualAttribute Table --- ")
        return False

    return True


def get_df_documentation(xl):
    if "Documentation" in xl.sheet_names:
        df_documentation = xl.parse("Documentation")
        return df_documentation


def preparse_sheets(dict_all_sheets, sheet):
    # df_sheet = xl.parse(sheet)
    df_sheet = dict_all_sheets.get(sheet)
    df_sheet = json.loads(df_sheet)
    df_sheet = pd.DataFrame.from_dict(df_sheet, orient='index')
    # df_sheet = df_sheet.sort_index()
    # create headers with 2 names - one name is not always unique
    header_shot = df_sheet.iloc[1].tolist()
    header_full = df_sheet.iloc[0].tolist()
    tuple_multi_headrs = list(zip(header_full,header_shot))
    multi_headers = pd.MultiIndex.from_tuples(tuple_multi_headrs, names=['full_name', 'short_name'])
    df_sheet.columns = multi_headers
    # print(df_sheet)
    # print(type(df_sheet))
    # df_sheet = df_sheet.drop(df_sheet.index[[0, 1]])
    # check for first empty row in sheet
    # index_nan = None
    list_index_nan= []
    for row in df_sheet.itertuples():
        row_unique_values = list(set(row))
        if len(row_unique_values) == 2:
            for item in row_unique_values:
                if any(i.isdigit() for i in str(item)):
                    # index_nan = item
                    list_index_nan.append(int(item))
                    #break
        # if index_nan:
        #     break
    index_nan = min(list_index_nan)

    # cut dataframe under first empty raw
    list_indexes = df_sheet.index.values.tolist()
    list_int_index = list(map(int, list_indexes))
    list_int_index.sort()
    dict_index_position = {}
    list_for_drop = []
    for i in list_indexes:
        dict_index_position[i] = list_indexes.index(i)
    list_index_for_drop = list_int_index[int(index_nan):]
    for li in list_index_for_drop:
        list_for_drop.append(dict_index_position.get(str(li)))
    for li in list_indexes:
        if li == "0" or li == "1":
            list_for_drop.append(dict_index_position.get(str(li)))
    df_sheet = df_sheet.drop(df_sheet.index[list_for_drop])
    return df_sheet


def get_dict_preparsed_data(list_unique_sheet_name, dict_all_sheets):
    dict_preparsed_data = {}
    for sheet in list_unique_sheet_name:
        df_preparsed = preparse_sheets(dict_all_sheets, sheet)
        dict_preparsed_data[sheet] = df_preparsed
    return dict_preparsed_data


def convert_list_attribute_values(list_attribute_values, datatype):
    new_list_attribute_values = []
    if datatype == "shortdate" or datatype == "MONTH/DAY/YEAR":
        for item in list_attribute_values:
            if item:
                item = str(item)
                if len(item) > 10:
                    item = item[:10]
                result = datetime.datetime.fromtimestamp(int(item)).strftime('%Y-%m-%d')
            # if isinstance(item, float):
            #     return list_attribute_values
            # if item.month < 10:
            #     month = "0%s" % str(item.month)
            # else:
            #     month = "%s" % str(item.month)
            # result = "%s-%s-%s" % (str(item.year), month, str(item.day))
                new_list_attribute_values.append(result)
    elif datatype == 'int_separated3' or datatype == "$":
        for item in list_attribute_values:
            item = str(item)
            if item and "$" in item:
                result = "".join(symb for symb in filter(lambda y: y.isdigit(), item))
                new_list_attribute_values.append(result)
            else:
                new_list_attribute_values.append(item)
    else:
        for item in list_attribute_values:
            new_list_attribute_values.append(str(item))
    return new_list_attribute_values


def get_correct_list(current_list, description):
    if isinstance(current_list, pd.Series):
        current_list = current_list.tolist()
    elif isinstance(current_list, pd.DataFrame):
        current_list = current_list[description].tolist()
    else:
        current_list = current_list.tolist()
    return current_list


def create_plan_annual_attr(dict_preparsed_data, field, sheet, current_plan_attribute, datatype, name):
    current_sheet = dict_preparsed_data.get(sheet)
    # get Plans:
    # by id - column Plan ID
    # print(current_sheet)
    # print(type(current_sheet))
    list_years = current_sheet[('Fiscal Year End', 'FYE')]
    list_years = get_correct_list(list_years, ('Fiscal Year End', 'FYE'))

    list_plans = []
    list_plans_full_name = current_sheet[('Internal Reason Plan ID #', 'Plan ID')]
    list_plans_full_name = get_correct_list(list_plans_full_name, ('Internal Reason Plan ID #', 'Plan ID'))
    # list_plans_full_name = current_sheet[('Internal Reason Plan ID #', 'Plan ID')].tolist()
    # print(list_plans_full_name)
    # sometimes we do not have Plan Id - get by Full_Name
    if None in list_plans_full_name:
        # print(list_plans_full_name)
        # print(current_sheet)
        list_plans_full_name = current_sheet[('Formal Plan Name', 'Full_Name')]
        list_plans_full_name = get_correct_list(list_plans_full_name, ('Formal Plan Name', 'Full_Name'))
        # list_plans_full_name = current_sheet[('Formal Plan Name', 'Full_Name')].tolist()
        for item in list_plans_full_name:
            plan = Plan.objects.get(display_name__iexact=item)
            list_plans.append(plan)
    else:
        for item in list_plans_full_name:
            # plan = Plan.objects.get(id=int(item))
            list_plans.append(Plan.objects.get(id=int(item)))
    try:
        # create total_list - with all row's data for creating new PlanAnnualAttribute
        list_attribute_values = current_sheet[(name, field)]
        list_attribute_values = get_correct_list(list_attribute_values, (name, field))
        # list_attribute_values = current_sheet[(name, field)].tolist()
        list_attribute_values_nan = current_sheet[(name, field)]

        if isinstance(list_attribute_values_nan, pd.Series):
            list_attribute_values_nan = list_attribute_values_nan.isnull().tolist()
        elif isinstance(list_attribute_values_nan, pd.DataFrame):
            list_attribute_values_nan = list_attribute_values_nan[(name, field)].tolist()
        else:
            list_attribute_values_nan = list_attribute_values_nan.isnull().tolist()

        # list_attribute_values_nan = current_sheet[(name, field)].isnull().tolist()
        list_attribute_values = convert_list_attribute_values(list_attribute_values, datatype)
        total_list = list(zip(list_attribute_values_nan, list_attribute_values, list_plans, list_years))

        # aList - data for bulk_create
        aList = [PlanAnnualAttribute(
            plan=val[2], year=str(val[3]),
            plan_attribute=current_plan_attribute, attribute_value=val[1]) for val in total_list if val[0] == False]
        try:
            PlanAnnualAttribute.objects.bulk_create(aList)
        except IntegrityError:
            # if you try to create PlanAnnualAttribute that already exists
            # print("PlanAnnualAttribute with this (plan_id, year, plan_attribute_id) already exists!  ")
            pass
    except KeyError:
        # KeyError may arise when we have row in sheet "Documentation" but no column with same data in another sheet
        pass


def parse_sheet_documentaion(dict_preparsed_data, df_documentation):
    all_headers_list = df_documentation.columns.values.tolist()
    headers_list = list(filter(lambda y: y is not None, map(lambda x:  x if 'Unnamed' not in x else None, all_headers_list)))
    # print(headers_list)
    # print(type(headers_list))
    # print(len(headers_list))

    # hardcode for Reason datasource
    if "Sheet" and "Field" and ("Data Type" or "datatype") and ("Description" or "name") in headers_list and len(headers_list) < 5:
        for row in df_documentation.itertuples():
            # print(row)
            # print(type(row))
            # print(dir(row))
            # # print(type(row.__dict__))

            sheet = getattr(row, 'Sheet')
            field = getattr(row, 'Field')

            # get name
            if 'name' in headers_list:
                name = getattr(row, 'name')
            elif "Description" in headers_list:
                name = getattr(row, 'Description')
            else:
                name = None

            # get datatype
            if "Data Type" in headers_list:
                datatype = getattr(row, '_4')
            elif "datatype" in headers_list:
                datatype = getattr(row, 'datatype')
            else:
                datatype = "text"

            # replace double quotes to single quotes in name:
            if name:
                name = name.replace('"', "'")
                plan_attr = PlanAttribute.objects.filter(name=name, data_source_id=3)
                # hardcode for Reason datasource
                # if not PlanAttribute.objects.filter(name=name, data_source_id=3).exists():
                #     print("does not exist")
                #     count += 1
                #     print(sheet, name, datatype, field)
                #     list_empty.append(name)
                #     print("===================<<<<<<<<<<<<<<")
                if plan_attr.exists() and plan_attr.count() == 1:
                    current_plan_attribute = PlanAttribute.objects.get(name=name, data_source_id=3)
                    create_plan_annual_attr(dict_preparsed_data, field, sheet, current_plan_attribute, datatype, name)

    # for row in df_documentation.itertuples():
    #     sheet = getattr(row, 'Sheet')
    #     field = getattr(row, 'Field')
    #     attribute_column_name = getattr(row, 'attribute_column_name')
    #     name = getattr(row, 'name')
    #     display_order = getattr(row, 'display_order')
    #     multiplier = getattr(row, 'multiplier')
    #     line_item_code = getattr(row, 'line_item_code')
    #     data_source = getattr(row, 'data_source')
    #     attribute_category_id = getattr(row, 'attribute_category_id')
    #     attribute_type = getattr(row, 'attribute_type')
    #     datatype = getattr(row, 'datatype')
    #
    #     # check PlanAttribute with line_item_code and data_source_id
    #     if PlanAttribute.objects.filter(
    #             line_item_code=line_item_code, data_source_id=data_source).exists():
    #         current_plan_attribute = PlanAttribute.objects.get(line_item_code=line_item_code, data_source_id=data_source)
    #     else:
    #         current_plan_attribute = PlanAttribute.objects.create(
    #             attribute_column_name=attribute_column_name,
    #             name=name,
    #             display_order=int(display_order),
    #             multiplier=multiplier,
    #             line_item_code=line_item_code,
    #             data_source_id=data_source,
    #             attribute_category_id=attribute_category_id,
    #             attribute_type=attribute_type,
    #             datatype=datatype
    #         )
    #     create_plan_annual_attr(dict_preparsed_data, field, sheet, current_plan_attribute, datatype, name)


@shared_task
def import_reason(dict_all_sheets, df_documentation, list_unique_sheet_name):
    df_documentation = json.loads(df_documentation)
    df_documentation = pd.DataFrame.from_dict(df_documentation, orient='index')
    dict_preparsed_data = get_dict_preparsed_data(list_unique_sheet_name, dict_all_sheets)
    parse_sheet_documentaion(dict_preparsed_data, df_documentation)
    # print(list_unique_sheet_name)
    # return True


@shared_task
def task_reporting_table():
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

        list_all_attribute_column_name = []
        for plan_attr in PlanAttribute.objects.all():
            if plan_attr.attribute_column_name is None or plan_attr.attribute_column_name == 'id' \
                    or " " in plan_attr.attribute_column_name or plan_attr.attribute_column_name == 'plan_id' \
                    or plan_attr.attribute_column_name == 'year':
                pass
            else:
                list_all_attribute_column_name.append(str(plan_attr.attribute_column_name))
        # only unique attribute_column_name
        list_all_attribute_column_name = list(set(list_all_attribute_column_name))
        for one_attr_col_name in list_all_attribute_column_name:
            cursor.execute('ALTER TABLE reporting_table ADD COLUMN {} varchar(300);'.format(str(one_attr_col_name)))

    # id__lte=500
    for plan in Plan.objects.all():
        scope_for_current_plan = PlanAnnualAttribute.objects.select_related('plan', 'plan_attribute').filter(plan=plan)
        if scope_for_current_plan.count() == 0:
            continue
        qs_years = scope_for_current_plan.values_list('year', flat=True)
        current_plan = scope_for_current_plan.first().plan

        def my_str(attr):
            if isinstance(attr, str):
                if not attr:
                    return "'%s'" % (str(attr))
                if " " in attr:
                    if "'" or '"' in attr:
                        return "'%s'" % (str(attr.replace("'", "").replace('"', '')))
                    return "'%s'" % (str(attr))
                return "'%s'" % (str(attr))
            elif attr:
                return attr
            return "NULL"

        for one_year in qs_years:
            try:
                with connection.cursor() as cursor:
                    str_insert = '''
                    INSERT INTO reporting_table
                    (plan_id, year, census_plan_id, name, display_name, year_of_inception, benefit_tier, year_closed,
                     web_site, soc_sec_coverage, soc_sec_coverage_notes, includes_state_employees, 
                     includes_local_employees, includes_safety_employees,includes_general_employees,
                     includes_teachers, intra_period_data_entity_id, intra_period_data_period_end_date, 
                     intra_period_data_period_type, gasb_68_type, state_gov_role, notes, system_assigned_employer_id,
                     latitude, longitude, admin_gov_id, employ_gov_id)
                    VALUES ({plan_id}, {one_year}, {census_plan_id}, {name}, {display_name}, {year_of_inception},
                    {benefit_tier},{year_closed}, {web_site}, {soc_sec_coverage}, {soc_sec_coverage_notes},
                     {includes_state_employees}, {includes_local_employees}, {includes_safety_employees},
                     {includes_general_employees},{includes_teachers}, {intra_period_data_entity_id},
                     {intra_period_data_period_end_date}, {intra_period_data_period_type}, {gasb_68_type},
                      {state_gov_role}, {notes}, {system_assigned_employer_id}, {latitude}, {longitude},
                      {admin_gov_id}, {employ_gov_id})
                    '''.format(
                        plan_id=current_plan.id,
                        one_year=one_year,
                        census_plan_id=my_str(current_plan.census_plan_id),
                        name=my_str(current_plan.name),
                        display_name=my_str(current_plan.display_name),
                        year_of_inception=my_str(current_plan.year_of_inception),
                        benefit_tier=my_str(current_plan.benefit_tier),
                        year_closed=my_str(current_plan.year_closed),
                        web_site=my_str(current_plan.web_site),
                        soc_sec_coverage=my_str(current_plan.soc_sec_coverage),
                        soc_sec_coverage_notes=my_str(current_plan.soc_sec_coverage_notes),
                        includes_state_employees=my_str(current_plan.includes_state_employees),
                        includes_local_employees=my_str(current_plan.includes_local_employees),
                        includes_safety_employees=my_str(current_plan.includes_safety_employees),
                        includes_general_employees=my_str(current_plan.includes_general_employees),
                        includes_teachers=my_str(current_plan.includes_teachers),
                        intra_period_data_entity_id=my_str(current_plan.intra_period_data_entity_id),
                        intra_period_data_period_end_date=my_str(current_plan.intra_period_data_period_end_date),
                        intra_period_data_period_type=my_str(current_plan.intra_period_data_period_type),
                        gasb_68_type=my_str(current_plan.gasb_68_type),
                        state_gov_role=my_str(current_plan.state_gov_role),
                        notes=my_str(current_plan.notes),
                        system_assigned_employer_id=my_str(current_plan.system_assigned_employer_id),
                        latitude=my_str(current_plan.latitude),
                        longitude=my_str(current_plan.longitude),
                        admin_gov_id=my_str(current_plan.admin_gov_id),
                        employ_gov_id=my_str(current_plan.employ_gov_id)
                    )
                    cursor.execute(str_insert)
            except ProgrammingError:
                pass
                # print("ProgrammingError-------->>> ", current_plan)

        with connection.cursor() as cursor:
            for one_attr in list_all_attribute_column_name:
                filter_scope = scope_for_current_plan.filter(plan_attribute__attribute_column_name=one_attr)
                if filter_scope.exists():
                    cur_pl_attr = scope_for_current_plan.filter(plan_attribute__attribute_column_name=one_attr).first().plan_attribute
                    for one_year in qs_years:
                        try:
                            case_exist = scope_for_current_plan.get(year=one_year, plan_attribute=cur_pl_attr)
                        except ObjectDoesNotExist:
                            continue
                        try:
                            attribute_value = my_str(case_exist.attribute_value)
                            str_update = '''
                            UPDATE reporting_table
                            SET {one_attr}={attribute_value}
                            WHERE plan_id={plan_id} AND year='{one_year}'
                            '''.format(
                                one_attr=one_attr,
                                attribute_value=attribute_value,
                                plan_id=current_plan.id,
                                one_year=one_year
                            )
                            cursor.execute(str_update)
                        except ProgrammingError:
                            pass
                        except Exception as e:
                            import logging
                            logging.exception(e)
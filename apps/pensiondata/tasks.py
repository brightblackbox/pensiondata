import re
import os
import time
import datetime
import json

import pandas as pd
import xlrd
from django.db.utils import  IntegrityError
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
    # df_sheet = df_sheet.drop(df_sheet.index[[0, 1]])
    # check for first empty row in sheet
    index_nan = None
    for row in df_sheet.itertuples():
        row_unique_values = list(set(row))
        if len(row_unique_values) == 2:
            for item in row_unique_values:
                if any(i.isdigit() for i in str(item)):
                    index_nan = item
                    break
        if index_nan:
            break
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
    # count = 0
    for sheet in list_unique_sheet_name:
        df_preparsed = preparse_sheets(dict_all_sheets, sheet)
        dict_preparsed_data[sheet] = df_preparsed
        # count += 1
        # if count == 1:
        #     break
    return dict_preparsed_data


def convert_list_attribute_values(list_attribute_values, datatype):
    new_list_attribute_values = []
    if datatype == "shortdate":
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
    elif datatype == 'int_separated3':
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


def create_plan_annual_attr(dict_preparsed_data, field, sheet, current_plan_attribute, datatype, name):
    current_sheet = dict_preparsed_data.get(sheet)
    # get Plans:
    # by name - column Full_Name

    list_plans_full_name = current_sheet[('Formal Plan Name', 'Full_Name')].tolist()
    list_years = current_sheet[('Fiscal Year End', 'FYE')].tolist()
    list_plans = []
    for item in list_plans_full_name:
        plan = Plan.objects.get(name__iexact=item)
        list_plans.append(plan)
    try:
        # create total_list - with all row's data for creating new PlanAnnualAttribute
        list_attribute_values = current_sheet[(name, field)].tolist()
        list_attribute_values_nan = current_sheet[(name, field)].isnull().tolist()
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
    for row in df_documentation.itertuples():
        sheet = getattr(row, 'Sheet')
        field = getattr(row, 'Field')
        attribute_column_name = getattr(row, 'attribute_column_name')
        name = getattr(row, 'name')
        display_order = getattr(row, 'display_order')
        multiplier = getattr(row, 'multiplier')
        line_item_code = getattr(row, 'line_item_code')
        data_source = getattr(row, 'data_source')
        attribute_category_id = getattr(row, 'attribute_category_id')
        attribute_type = getattr(row, 'attribute_type')
        datatype = getattr(row, 'datatype')

        # check PlanAttribute with line_item_code and data_source_id
        if PlanAttribute.objects.filter(
                line_item_code=line_item_code, data_source_id=data_source).exists():
            current_plan_attribute = PlanAttribute.objects.get(line_item_code=line_item_code, data_source_id=data_source)
        else:
            current_plan_attribute = PlanAttribute.objects.create(
                attribute_column_name=attribute_column_name,
                name=name,
                display_order=int(display_order),
                multiplier=multiplier,
                line_item_code=line_item_code,
                data_source_id=data_source,
                attribute_category_id=attribute_category_id,
                attribute_type=attribute_type,
                datatype=datatype
            )
        create_plan_annual_attr(dict_preparsed_data, field, sheet, current_plan_attribute, datatype, name)


@shared_task
def import_reason(dict_all_sheets, df_documentation, list_unique_sheet_name):
    df_documentation = json.loads(df_documentation)
    df_documentation = pd.DataFrame.from_dict(df_documentation, orient='index')
    dict_preparsed_data = get_dict_preparsed_data(list_unique_sheet_name, dict_all_sheets)
    parse_sheet_documentaion(dict_preparsed_data, df_documentation)
    # return True

import re
from django.contrib import admin
from django.db.models import F, Count, Case, When, Value, BooleanField
import json
from django.conf.urls import url
from django.db.models.query import QuerySet

from .models import Plan, Government, County, State, GovernmentType, PlanAttribute, DataSource, \
    PlanAnnualAttribute, AttributeCategory, \
    GovernmentAttribute, GovernmentAnnualAttribute, PresentationExport, ExportGroup, PlanBenefitDesign, PlanInheritance,ReportingTable, \
    PlanAnnualMasterAttribute, PlanAttributeMaster, PlanMasterAttributeNames, MapCharts

from .models import GovernmentAttrSummary
from .tasks import generate_calculated_fields, generate_calculated_fields_null


from moderation.admin import ModerationAdmin

from django.forms import TextInput, Textarea
from django.db import models
from django.shortcuts import redirect
from django_extensions.admin import ForeignKeyAutocompleteAdmin

from .mixins import ImportMixin


class ForeignKeyCacheMixin(object):
    """
    Cache foreignkey choices in the request object to prevent unnecessary queries.
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super(ForeignKeyCacheMixin, self).formfield_for_foreignkey(db_field, **kwargs)
        cache = getattr(request, 'db_field_cache', {})
        if cache.get(db_field.name):
            formfield.choices = cache[db_field.name]
        else:
            formfield.choices.field.cache_choices = True
            formfield.choices.field.choice_cache = [
                formfield.choices.choice(obj) for obj in formfield.choices.queryset.all()
            ]
            request.db_field_cache = cache
            request.db_field_cache[db_field.name] = formfield.choices
        return formfield


class CountyAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': [field.name for field in County._meta.fields if field.name != 'id']})
    ]
    list_display = ['name', 'state']
    list_filter = ['government__state']
    search_fields = ['name', 'government__state']

    list_select_related = True

    def state(self, obj):
        return obj.government.state

    def get_queryset(self, request):
        """
        Filter the objects displayed in the change_list to only
        display those for the currently signed in user.
        """
        qs = super(CountyAdmin, self).get_queryset(request)
        return qs.exclude(name='Not Applicable')


admin.site.register(County, CountyAdmin)


class StateAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': [field.name for field in State._meta.fields if field.name != 'id']})
    ]
    list_display = ('name', 'state_abbreviation')
    list_filter = ['name']
    search_fields = ['name']


admin.site.register(State, StateAdmin)


class GovernmentTypeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': [field.name for field in GovernmentType._meta.fields if field.name != 'id']})
    ]
    list_display = ('id', 'level')
    list_filter = ['level']
    search_fields = ['level']


admin.site.register(GovernmentType, GovernmentTypeAdmin)


class GovernmentAdmin(ModerationAdmin):
    model = Government

    fieldsets = [
        (None, {'fields': [field.name for field in Government._meta.fields if field.name != 'id']})
    ]
    list_display = ['__str__', 'government_type', 'county', 'state']
    list_filter = ['government_type', 'state']

    list_select_related = ('government_type', 'county', 'state', )
    list_per_page = 50
    search_fields = ['name']
    ordering = ['name']

    def get_actions(self, request):
        actions = super(ModerationAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    # customized change view:
    change_form_template = 'admin/gov_detail.html'
    add_form_template = 'admin/change_form.html'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if self.admin_integration_enabled:
            self.send_message(request, object_id)

        extra_context = extra_context or {}

        government = Government.objects.get(id=object_id)

        gov_annual_objs = GovernmentAnnualAttribute.objects.filter(government=government)

        if gov_annual_objs.count() < 1:
            print('here')
            return super(GovernmentAdmin, self).change_view(request, object_id, form_url, extra_context)

        category_list = AttributeCategory.objects.order_by('name')
        datasource_list = DataSource.objects.order_by('name')
        year_list = gov_annual_objs.order_by('year').values('year').distinct()

        attr_id_list = gov_annual_objs.values_list('government_attribute__id', flat=True).distinct()
        attr_list = GovernmentAttrSummary.objects.filter(id__in=attr_id_list).order_by("name")
        all_attr_list = GovernmentAttrSummary.objects\
            .values('id', 'name', 'attribute_type', 'data_source_id', 'data_source_name', 'attribute_category_name', 'calculated_rule')

        gov_annual_objs = gov_annual_objs.values('id', 'year', 'attribute_value', 'is_from_source', 'government_attribute__id')

        extra_context['attr_list'] = attr_list
        extra_context['category_list'] = category_list
        extra_context['datasource_list'] = datasource_list
        extra_context['year_list'] = year_list
        extra_context['year_range'] = range(1932, 2020)

        extra_context['all_attr_list'] = json.dumps(list(all_attr_list))
        extra_context['gov_annual_data'] = json.dumps(list(gov_annual_objs))

        return super(GovernmentAdmin, self).change_view(request, object_id, form_url, extra_context)


admin.site.register(Government, GovernmentAdmin)


class PlanAdmin(ImportMixin, ModerationAdmin):
    model = Plan

    list_display = ['id', 'census_plan_id', 'name', 'display_name', ]
    list_filter = ['admin_gov__state__name']
    list_per_page = 30
    ordering = ['admin_gov__state__id']
    search_fields = ['display_name', 'name']
    raw_id_fields = ['admin_gov', 'employ_gov']

    list_select_related = ('admin_gov', 'admin_gov__state',)

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'80'})}
    }

    def state(self, obj):
        return obj.admin_gov.state

    def get_actions(self, request):
        actions = super(ModerationAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    # customized change view:
    change_form_template = 'admin/plan_detail.html'
    add_form_template = 'admin/change_form.html'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if self.admin_integration_enabled:
            self.send_message(request, object_id)

        extra_context = extra_context or {}

        plan = Plan.objects.get(id=object_id)

        # attr_list = PlanAttribute.objects.filter(annual_attrs__plan=plan)\
        #     .select_related('attribute_category', 'data_source').distinct()

        category_list = AttributeCategory.objects.order_by('name')

        if (request.session.get('plan_column_state_admin')):
            selected_data_sources = request.session.get('plan_column_state_admin').get('source')
        else:
            # get all data from all Data source by default
            selected_data_sources = list(DataSource.objects.filter().values_list("id", flat=True))
        datasource_list = DataSource.objects.all().annotate( \
            # 'selected' is helpful in checking the options in the checkboxes
            selected=Case(
                When(id__in=selected_data_sources, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).order_by('name')

        plan_annual_objs = PlanAnnualAttribute.objects \
            .filter(plan=plan) \
            .select_related('plan_attribute') \
            .select_related('plan_attribute__attribute_category') \
            .select_related('plan_attribute__data_source')

        if plan_annual_objs.count() < 1:
            return super(PlanAdmin, self).change_view(request, object_id, form_url, extra_context)

        year_list = plan_annual_objs.order_by('year').values('year').distinct()

        plan_annual_data \
            = plan_annual_objs \
            .values('id',
                    'year',
                    'plan_attribute__id',
                    'plan_attribute__data_source__id',
                    'plan_attribute__attribute_category__id',
                    'attribute_value',
                    'is_from_source') \
            .annotate(
                    attribute_id=F('plan_attribute__id'),
                    data_source_id=F('plan_attribute__data_source__id'),
                    category_id=F('plan_attribute__attribute_category__id'))

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

        all_attr_list = PlanAttribute.objects.all() \
            .values(
                'id', 'name', 'attribute_type', 'calculated_rule', 'attribute_category__name', 'data_source__name'
            ) \
            .annotate(
                category=F('attribute_category__name'),
                data_source=F('data_source__name')
            ) \
            .order_by("name")

        extra_context['attr_list'] = attr_list
        extra_context['category_list'] = category_list
        extra_context['datasource_list'] = datasource_list
        extra_context['year_list'] = year_list
        extra_context['year_range'] = range(1932, 2020)

        extra_context['plan_annual_data'] = json.dumps(list(plan_annual_data))
        extra_context['all_attr_list'] = json.dumps(list(all_attr_list))

        return super(PlanAdmin, self).change_view(request, object_id, form_url, extra_context)

admin.site.register(Plan, PlanAdmin)


class GovernmentAttributeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': [field.name for field in GovernmentAttribute._meta.fields if field.name != 'id']})
    ]

    list_display = ['name', 'data_source', 'datatype', 'attribute_category', 'line_item_code',
                    'attribute_column_name', 'multiplier', ]
    list_select_related = ('attribute_category', 'data_source')
    list_filter = ['data_source', 'attribute_category', 'attribute_type']
    list_per_page = 50
    search_fields = ['name']

    change_form_template = 'admin/attribute_detail.html'
    add_form_template = 'admin/attribute_detail.html'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}

        # static_attr_list = GovernmentAttrSummary.objects.filter(attribute_type='static').values('id', 'name').order_by("name")
        # non_master_attrs = GovernmentAttrSummary.objects.exclude(data_source_id=0).order_by("name")  # NOTE: pension data

        static_attr_list = GovernmentAttribute.objects.filter(attribute_type='static').values('id', 'name').order_by("name")
        non_master_attrs = GovernmentAttribute.objects.exclude(data_source__id=0) \
            .order_by('name') \
            .select_related('data_source')  # NOTE: pension data

        try:
            obj = GovernmentAttribute.objects.get(id=object_id)

            extra_context['attrs_for_master'] = obj.attributes_for_master
            if obj.attributes_for_master is not None:
                extra_context['attrs_for_master'] = obj.attributes_for_master.split(",")

        except GovernmentAttribute.DoesNotExist:
            extra_context['attrs_for_master'] = []

        extra_context['static_attr_list'] = json.dumps(list(static_attr_list))
        extra_context['non_master_attrs'] = non_master_attrs

        return super(GovernmentAttributeAdmin, self).change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}

        static_attr_list = GovernmentAttribute.objects.filter(attribute_type='static').values('id', 'name').order_by(
            "name")
        non_master_attrs = GovernmentAttribute.objects.exclude(data_source__id=0) \
            .order_by('name') \
            .select_related('data_source')  # NOTE: pension data

        extra_context['static_attr_list'] = json.dumps(list(static_attr_list))
        extra_context['non_master_attrs'] = non_master_attrs
        extra_context['attrs_for_master'] = []

        return super(GovernmentAttributeAdmin, self).add_view(request, form_url, extra_context)


admin.site.register(GovernmentAttribute, GovernmentAttributeAdmin)


class PlanAttributeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': [field.name for field in PlanAttribute._meta.fields if field.name != 'id']})
    ]

    list_display = ['name', 'data_source', 'datatype', 'attribute_category', 'line_item_code',
                    'attribute_column_name', 'multiplier', ]
    list_select_related = ('attribute_category', 'data_source')
    list_filter = ['data_source', 'attribute_category', 'attribute_type']
    list_per_page = 50
    search_fields = ['name']

    change_form_template = 'admin/attribute_detail.html'
    add_form_template = 'admin/attribute_detail.html'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}

        static_attr_list = PlanAttribute.objects.filter(attribute_type='static').values('id', 'name').order_by("name")
        non_master_attrs = PlanAttribute.objects.exclude(data_source__id=0)\
            .order_by('name') \
            .select_related('data_source')  # NOTE: pension data

        try:
            obj = PlanAttribute.objects.get(id=object_id)

            extra_context['attrs_for_master'] = obj.attributes_for_master
            if obj.attributes_for_master is not None:
                extra_context['attrs_for_master'] = obj.attributes_for_master.split(",")

        except PlanAttribute.DoesNotExist:
            extra_context['attrs_for_master'] = []

        extra_context['static_attr_list'] = json.dumps(list(static_attr_list))
        extra_context['non_master_attrs'] = non_master_attrs

        return super(PlanAttributeAdmin, self).change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}

        static_attr_list = PlanAttribute.objects.filter(attribute_type='static').values('id', 'name').order_by("name")
        non_master_attrs = PlanAttribute.objects.exclude(data_source__id=0) \
            .order_by('name') \
            .select_related('data_source')  # NOTE: pension data

        extra_context['static_attr_list'] = json.dumps(list(static_attr_list))
        extra_context['non_master_attrs'] = non_master_attrs
        extra_context['attrs_for_master'] = []

        return super(PlanAttributeAdmin, self).add_view(request, form_url, extra_context)


class GenerateCalculatedAttributeData(PlanAttribute):
    class Meta:
        proxy = True
        verbose_name = "Calculated Attribute"


admin.site.register(PlanAttribute, PlanAttributeAdmin)


def calculate(modeladmin, request, queryset):
    """
    This function is used for parsing string like:

    #611##-##587##*##%2%#
    (Total Number of Members - Total Number of actives * 2)
    In this format field calculated_rule is stared in database.
    +,-,/,* - math operations,
    #611# - id of Plan Attribute,
    %2% - digit

    Note, that position of ID's Plan Attribute could change!

    We convert string #611##-##587##*##%2%#
    to list ['611', '-', '587', '*', '%2%']

    Get indexies of ID's Plan Attribute - [0,2]


    """
    list_ids = [qs.id for qs in queryset]
    task_calculated_id = generate_calculated_fields.delay(list_ids=list_ids)
    task_calculated_id = task_calculated_id.id
    request.task_id = task_calculated_id
    calculate.task_calculated_id = task_calculated_id


def null_recalculate(modeladmin, request, queryset):
    list_ids = [qs.id for qs in queryset]
    calculate_null_task = generate_calculated_fields_null.delay(list_ids=list_ids)
    calculate_null_task = calculate_null_task.id
    null_recalculate.calculate_null_task = calculate_null_task


calculate.short_description = "Calculate selected items"
null_recalculate.short_description = "ReCalculate with NULL selected items"


class PlanAttributeCalculatedAdmin(PlanAttributeAdmin):
    actions = [calculate, null_recalculate]

    def get_queryset(self, request):
        return self.model.objects.filter(attribute_type='calculated')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        if "task_calculated_id" in dir(calculate):
            extra_context['task_calculated_id'] = calculate.task_calculated_id
        if "calculate_null_task" in dir(null_recalculate):
            extra_context['task_calculated_id'] = null_recalculate.calculate_null_task
        extra_context['some_var'] = 'This is what I want to show'
        return super(PlanAttributeAdmin, self).changelist_view(request, extra_context=extra_context)

admin.site.register(GenerateCalculatedAttributeData, PlanAttributeCalculatedAdmin)


class AttributeCategoryAdmin(admin.ModelAdmin):
    """
    Category Admin page
    """
    list_display = ['id', 'name']
    list_editable = ['name']


admin.site.register(AttributeCategory, AttributeCategoryAdmin)


class DataSourceAdmin(admin.ModelAdmin):
    """
    DataSource Admin page
    """
    list_display = ['id', 'name', 'trust_level', 'private']
    list_editable = ['name', 'trust_level']


admin.site.register(DataSource, DataSourceAdmin)


class PlanAnnualAttributeAdmin(ImportMixin, admin.ModelAdmin):

    def changelist_view(self, request, extra_context=None):
        """
        The 'change list' admin view for this model.
        """

        return redirect('/admin/%s/%s/import/' % self.get_model_info())


admin.site.register(PlanAnnualAttribute, PlanAnnualAttributeAdmin)


class PlanBenefitDesignAdmin(admin.ModelAdmin):
    list_display = ['id', "plan_name", "tier", "occupation"]
    search_fields = ["plan_name"]
    ordering = "id",


class PlanInheritanceAdmin(admin.ModelAdmin):
    list_display = ["id", "child_plan", "parent_plan"]
    raw_id_fields = ["child_plan", "parent_plan"]
    ordering = "id",


class ReportingTableAdmin( admin.ModelAdmin):
    raw_id_fields = ['plan', 'admin_gov', 'employ_gov']

    change_list_template = 'admin/reportingtable.html'


    # def get_model_info(self):
    #     app_label = self.model._meta.app_label
    #     try:
    #         return ( app_label, self.model._meta.model_name, )
    #     except AttributeError:
    #         return ( app_label, self.model._meta.module_name, )
    #
    # def changelist_view(self, request, extra_context=None):
    #     """
    #     The 'change list' admin view for this model.
    #     """
    #     print(self.get_model_info())
    #     print('=+++++++++')
    #
    #     return redirect('/admin/%s/%s/reportingtable/' % self.get_model_info())

class MapChartsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'stored_procedure', 'display_order',)
    list_display_links = ('id', 'title',)
    ordering = ('display_order',)

admin.site.register(MapCharts, MapChartsAdmin)

class PlanAnnualMasterAttributeAdmin(admin.ModelAdmin):
    raw_id_fields = ('plan',)

    fields = ('year', 'attribute_value', 'plan', 'plan_attribute')
    list_display = ('year', 'attribute_value', 'plan', 'plan_attribute')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'plan_attribute':
            kwargs['queryset'] = PlanAttribute.objects.all().order_by('name')

        return super(PlanAnnualMasterAttributeAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

class PlanAttributeMasterAdmin(admin.ModelAdmin):

    list_display = ('master_attribute', 'plan_attribute', 'priority')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'master_attribute':
            kwargs['queryset'] = PlanMasterAttributeNames.objects.all().order_by('name')

        if db_field.name == 'plan_attribute':
            kwargs['queryset'] = PlanAttribute.objects.all().order_by('name')

        return super(PlanAttributeMasterAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(PresentationExport)
admin.site.register(ExportGroup)
admin.site.register(PlanBenefitDesign, PlanBenefitDesignAdmin)
admin.site.register(PlanInheritance, PlanInheritanceAdmin)
admin.site.register(ReportingTable, ReportingTableAdmin)
admin.site.register(PlanAnnualMasterAttribute, PlanAnnualMasterAttributeAdmin)
admin.site.register(PlanMasterAttributeNames)
admin.site.register(PlanAttributeMaster, PlanAttributeMasterAdmin)

###############################################################################
# To register new model, you also need to add it to ADMIN_REORDER at settings.
###############################################################################

from django.contrib import admin
from django.db.models import F, Count
import json

from .models import Plan, Government, County, State, GovernmentType, PlanAttribute, \
    PlanAnnualAttribute, PlanAttributeMaster, PlanAttributeCategory, PlanAnnual, \
    GovernmentAttribute, GovernmentAnnualAttribute, GovernmentAttributeCategory

from .models import CensusAnnualAttribute, DataSource

from moderation.admin import ModerationAdmin

from django.forms import TextInput, Textarea
from django.db import models


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


class CensusAnnualAttributeInline(admin.TabularInline):
    model = CensusAnnualAttribute
    extra = 0
    exclude = ('id', )
    readonly_fields = ('year',)

class DataSourceAdmin(admin.ModelAdmin):
    model = DataSource
    extra = 0

admin.site.register(DataSource, DataSourceAdmin)

class PlanAdmin(ModerationAdmin):
    model = Plan

    list_display = ['display_name', 'state']
    list_filter = ['admin_gov__state__name']
    list_per_page = 50
    ordering = ['admin_gov__state__id']
    search_fields = ['display_name']

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

    class Media:
        css = {"all": ("css/admin.css",)}

    # customized change view:
    change_form_template = 'admin/plan-detail.html'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if self.admin_integration_enabled:
            self.send_message(request, object_id)

        extra_context = extra_context or {}

        plan = Plan.objects.get(id=object_id)

        # attr_list = PlanAttribute.objects.filter(annual_attrs__plan=plan)\
        #     .select_related('plan_attribute_category', 'data_source').distinct()

        category_list = PlanAttributeCategory.objects.order_by('name')
        datasource_list = DataSource.objects.order_by('name')

        plan_annual_objs = PlanAnnualAttribute.objects \
            .filter(plan=plan) \
            .select_related('plan_attribute') \
            .select_related('plan_attribute__plan_attribute_category') \
            .select_related('plan_attribute__data_source')

        year_list = plan_annual_objs.order_by('year').values('year').distinct()

        plan_annual_data \
            = plan_annual_objs \
            .values('id',
                    'year',
                    'plan_attribute__id',
                    'plan_attribute__data_source__id',
                    'plan_attribute__plan_attribute_category__id',
                    'attribute_value') \
            .annotate(
                    attribute_id=F('plan_attribute__id'),
                    data_source_id=F('plan_attribute__data_source__id'),
                    category_id=F('plan_attribute__plan_attribute_category__id'))

        attr_list = plan_annual_objs.values(
            'plan_attribute__id',
            'plan_attribute__name',
            'plan_attribute__data_source__id',
            'plan_attribute__data_source__name',
            'plan_attribute__plan_attribute_category__id',
            'plan_attribute__plan_attribute_category__name'
        ).annotate(
            attribute_id=F('plan_attribute__id'),
            attribute_name=F('plan_attribute__name'),
            data_source_id=F('plan_attribute__data_source__id'),
            data_source_name=F('plan_attribute__data_source__name'),
            category_id=F('plan_attribute__plan_attribute_category__id'),
            category_name=F('plan_attribute__plan_attribute_category__name')
        ).distinct().order_by('category_name', 'attribute_name')

        all_attr_list = PlanAttribute.objects.all() \
            .values(
                'id', 'name', 'attribute_type', 'calculated_rule', 'plan_attribute_category__name'
            ) \
            .annotate(
                category=F('plan_attribute_category__name')
            ) \
            .order_by("name")

        extra_context['attr_list'] = attr_list
        extra_context['category_list'] = category_list
        extra_context['datasource_list'] = datasource_list
        extra_context['year_list'] = year_list
        extra_context['year_range'] = range(1990, 2020)

        extra_context['plan_annual_data'] = json.dumps(list(plan_annual_data))
        extra_context['all_attr_list'] = json.dumps(list(all_attr_list))

        return super(PlanAdmin, self).change_view(request, object_id, form_url, extra_context)


admin.site.register(Plan, PlanAdmin)


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


#### STATE
class StateAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': [field.name for field in State._meta.fields if field.name != 'id']})
    ]
    list_display = ('name', 'state_abbreviation')
    list_filter = ['name']
    search_fields = ['name']


admin.site.register(State, StateAdmin)


#### GOVERNMENT TYPE
class GovernmentTypeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': [field.name for field in GovernmentType._meta.fields if field.name != 'id']})
    ]
    list_display = ('id', 'level')
    list_filter = ['level']
    search_fields = ['level']


admin.site.register(GovernmentType, GovernmentTypeAdmin)


#### GOVERNMENT TYPE
class GovernmentAdmin(admin.ModelAdmin):
    model = Government

    fieldsets = [
        (None, {'fields': [field.name for field in Government._meta.fields if field.name != 'id']})
    ]
    list_display = ['name', 'government_type', 'county', 'state']
    list_filter = ['government_type', 'state']
    list_per_page = 50
    search_fields = ['name', 'county', 'state']
    ordering = ['state', 'government_type', 'county']


admin.site.register(Government, GovernmentAdmin)

#### GOVERNMENT Attribute 
class GovernmentAttributeAdmin(admin.ModelAdmin):
    model = GovernmentAttribute

    list_display = ['name']

admin.site.register(GovernmentAttribute, GovernmentAttributeAdmin)

#### GOVERNMENT Attribute Category
class GovernmentAttributeCategoryAdmin(admin.ModelAdmin):
    model = GovernmentAttributeCategory

    list_display = ['name']

admin.site.register(GovernmentAttributeCategory, GovernmentAttributeCategoryAdmin)

#### GOVERNMENT Annual Attribute
class GovernmentAnnualAttributeAdmin(admin.ModelAdmin):
    model = GovernmentAnnualAttribute

    list_display = ['government_attribute', 'year', 'value']

admin.site.register(GovernmentAnnualAttribute, GovernmentAnnualAttributeAdmin)


class PlanAttributeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': [field.name for field in PlanAttribute._meta.fields if field.name != 'id']})
    ]

    list_display = ['name', 'data_source', 'datatype', 'plan_attribute_category', 'display_order',
                    'attribute_column_name', 'multiplier', 'attribute_type', ]
    list_select_related = ('plan_attribute_category', 'data_source')
    list_filter = ['data_source', 'plan_attribute_category', 'attribute_type']
    list_per_page = 50
    search_fields = ['name']

    change_form_template = 'admin/plan_attribute_detail.html'
    add_form_template = 'admin/plan_attribute_detail.html'

    class Media:
        css = {"all": ("css/admin.css",)}

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}

        static_attr_list = PlanAttribute.objects.filter(attribute_type='static').values('id', 'name').order_by("name")

        extra_context['static_attr_list'] = json.dumps(list(static_attr_list))

        return super(PlanAttributeAdmin, self).change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}

        static_attr_list = PlanAttribute.objects.filter(attribute_type='static').values('id', 'name').order_by("name")

        extra_context['static_attr_list'] = json.dumps(list(static_attr_list))

        return super(PlanAttributeAdmin, self).add_view(request, form_url, extra_context)


admin.site.register(PlanAttribute, PlanAttributeAdmin)


#### PLAN ATTRIBUTE MASTER
class PlanAttributeMasterAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': [field.name for field in PlanAttribute._meta.fields if field.name != 'id']})
    ]

    list_display = ['id', 'name', 'datatype', 'plan_attribute_category', 'display_order', 'attribute_column_name']
    list_select_related = True
    list_filter = ['plan_attribute_category']
    list_per_page = 50
    search_fields = ['name']


admin.site.register(PlanAttributeMaster, PlanAttributeMasterAdmin)


#### PLAN ATTRIBUTE MASTER
class PlanAttributeCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    list_editable = ['name']


admin.site.register(PlanAttributeCategory, PlanAttributeCategoryAdmin)

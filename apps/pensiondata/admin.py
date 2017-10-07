from django.contrib import admin
from django.db.models import F
import json

from .models import Plan, Government, County, State, GovernmentType, PlanAttribute, \
    PlanAnnualAttribute, PlanAttributeMaster, PlanAttributeCategory, PlanAnnual

from .models import CensusAnnualAttribute


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


# class PPDAnnualAttributeInline(admin.TabularInline):
#     model = PPDAnnualAttribute
#     extra = 0
#     exclude = ('id', )
#     readonly_fields = ('year',)


class PlanAnnualAttributeInline(ForeignKeyCacheMixin, admin.TabularInline):

    model = PlanAnnualAttribute
    extra = 0

    readonly_fields = ['year', 'source', 'category', 'attribute']
    fields = ['year', 'source', 'category', 'attribute', 'attribute_value']
    ordering = ['-year']

    def attribute(self, obj):
        return obj.plan_attribute.attribute

    def source(self, obj):
        return obj.plan_attribute.data_source.name

    def category(self, obj):
        return obj.plan_attribute.plan_attribute_category.name

    # template = "admin/plan-detail.html"

    def get_queryset(self, request):
        qs = PlanAnnualAttribute.objects.select_related(
                                            'plan_attribute',
                                            'plan_attribute__data_source',
                                            'plan_attribute__plan_attribute_category'
        )
        return qs


class PlanAdmin(admin.ModelAdmin):
    model = Plan

    list_display = ['name', 'state']
    list_filter = ['admin_gov__state__name']
    list_per_page = 50
    ordering = ['admin_gov__state__id']
    search_fields = ['name']

    # fieldsets = (
    #     (None, {
    #         'fields': (
    #             'census_plan_id', 'name', 'display_name',
    #             ('year_of_inception', 'benefit_tier', 'year_closed'),
    #             'web_site', 'admin_gov',
    #             ('soc_sec_coverage', 'soc_sec_coverage_notes', ),
    #             ('includes_state_employees', 'includes_local_employees', 'includes_safety_employees', 'includes_general_employees', 'includes_teachers'),
    #             ('intra_period_data_entity_id', 'intra_period_data_period_end_date'),
    #             'intra_period_data_period_type', 'gasb_68_type', 'state_gov_role', 'notes'
    #         )
    #     }),
    # )

    list_select_related = True

    # inlines = [PlanAnnualAttributeInline, ]

    def state(self, obj):
        return obj.admin_gov.state

    class Media:
        css = {"all": ("css/planadmin.css",)}

    # def get_formsets_with_inlines(self, request, obj=None):
    #     for inline in self.get_inline_instances(request, obj):
    #         inline.cached_plan_attributes = [(i.pk, str(i)) for i in PlanAttribute.objects.all()]
    #         yield inline.get_formset(request, obj), inline

    # customized change view:
    change_form_template = 'admin/plan-detail.html'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}

        categories = PlanAttributeCategory.objects.values('id', 'name').order_by("name")
        plan_annual_attrs \
            = PlanAnnualAttribute.objects.filter(plan__id=object_id)\
            .values('id',
                    'year',
                    'plan_attribute__name',
                    'plan_attribute__data_source__name',
                    'plan_attribute__plan_attribute_category__id',
                    'plan_attribute__plan_attribute_category__name',
                    'attribute_value') \
            .annotate(
                        attribute=F('plan_attribute__name'),
                        data_source=F('plan_attribute__data_source__name'),
                        category_id=F('plan_attribute__plan_attribute_category__id'),
                        category_name=F('plan_attribute__plan_attribute_category__name'))\
            .order_by('category_name', '-year')

        extra_context['categories_queryset'] = categories
        extra_context['categories_json'] = json.dumps(list(categories))
        extra_context['plan_annual_attrs'] = json.dumps(list(plan_annual_attrs))

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
    fieldsets = [
        (None, {'fields': [field.name for field in Government._meta.fields if field.name != 'id']})
    ]
    list_display = ['name', 'government_type', 'county', 'state']
    list_filter = ['government_type', 'state']
    list_per_page = 50
    search_fields = ['name', 'county', 'state']
    ordering = ['state', 'government_type', 'county']


admin.site.register(Government, GovernmentAdmin)


#### PLAN ATTRIBUTE
class PlanAttributeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': [field.name for field in PlanAttribute._meta.fields if field.name != 'id']})
    ]

    list_display = ['name', 'data_source', 'datatype', 'plan_attribute_category', 'display_order',
                    'attribute_column_name', 'multiplier', 'attribute_type', ]
    list_select_related = True
    list_filter = ['data_source', 'plan_attribute_category', 'attribute_type']
    list_per_page = 50
    search_fields = ['name']


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


class PlanAnnualAdmin(admin.ModelAdmin):
    list_display = ['plan', 'year', 'government_id']


admin.site.register(PlanAnnual, PlanAnnualAdmin)


class PlanAnnualAttributeAdmin(admin.ModelAdmin):
    list_display = ['plan', 'year', 'plan_attribute', 'attribute_value']


admin.site.register(PlanAnnualAttribute, PlanAnnualAttributeAdmin)

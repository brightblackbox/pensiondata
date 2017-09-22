from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django import forms
from nested_admin import NestedTabularInline, NestedStackedInline, NestedModelAdmin
import copy

#### MODELS
from .models import Plan, County, Government, County, State, GovernmentType, PlanAttribute, \
    PlanAnnualAttribute, PlanAttributeMaster, PlanAttributeCategory

### THESE ARE STILL UNDER CONSTRUCTION
from .models import CensusAnnualAttribute, PPDAnnualAttribute  ##, PlanAnnualAttribute


### MIXIN TO REDUCE EXTRANEOUS QUERIES IN INLINE
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


### CENSUS PLAN ANNUAL ATTRIBUTES
class CensusAnnualAttributeInline(admin.TabularInline):
    model = CensusAnnualAttribute
    extra = 0


### CENSUS PLAN ANNUAL ATTRIBUTES
class PPDAnnualAttributeInline(admin.TabularInline):
    model = PPDAnnualAttribute
    extra = 0


### PLAN ANNUAL ATTRIBUTES
class PlanAnnualAttributeInline(ForeignKeyCacheMixin, admin.TabularInline):
    model = PlanAnnualAttribute
    extra = 0

    readonly_fields = ['year', 'source', 'attribute', 'attribute_value']
    fields = ['year', 'source', 'attribute', 'attribute_value']
    ordering = ['-year']

    # template = "admin/pivot.html"

    def attribute(self, obj):
        return obj.plan_attribute.attribute

    def source(self, obj):
        return obj.plan_attribute.data_source.name

    def get_queryset(self, request):
        print(request)
        qs = PlanAnnualAttribute.objects.select_related('plan_attribute', 'plan_attribute__data_source')
        return qs


### PLAN
class PlanAdmin(admin.ModelAdmin):
    model = Plan

    list_display = ['name', 'state']
    list_filter = ['admin_gov__state__name']
    list_per_page = 50
    ordering = ['admin_gov__state__id']
    search_fields = ['name']

    list_select_related = True

    def state(self, obj):
        return obj.admin_gov.state

    # inlines = [PPDAnnualAttributeInline]

    class Media:
        css = {"all": ("css/planadmin.css",)}

        # def get_formsets_with_inlines(self, request, obj=None):
        #     for inline in self.get_inline_instances(request, obj):
        #         inline.cached_plan_attributes = [(i.pk, str(i)) for i in PlanAttribute.objects.all()]
        #         yield inline.get_formset(request, obj), inline


admin.site.register(Plan, PlanAdmin)


#### COUNTY
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

    list_display = ['id', 'data_source', 'name', 'datatype', 'plan_attribute_category', 'display_order',
                    'attribute_column_name', 'multiplier', 'plan_attribute_master']
    list_select_related = True
    list_filter = ['data_source', 'plan_attribute_category']
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


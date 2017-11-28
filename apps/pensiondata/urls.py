from django.conf.urls import url

from .views import edit_plan_annual_attr, delete_plan_annual_attr, add_plan_annual_attr, save_checklist, \
                    edit_gov_annual_attr, delete_gov_annual_attr, add_gov_annual_attr


app_name = 'pensiondata'

urlpatterns = [

    url(r'^plan_annual_attr/edit/$', edit_plan_annual_attr, name="edit_plan_annual_attr"),
    url(r'^plan_annual_attr/delete/$', delete_plan_annual_attr, name="delete_plan_annual_attr"),
    url(r'^plan_annual_attr/add/$', add_plan_annual_attr, name='add_plan_annual_attr'),

    url(r'^gov_annual_attr/edit/$', edit_gov_annual_attr, name="edit_gov_annual_attr"),
    url(r'^gov_annual_attr/delete/$', delete_gov_annual_attr, name="delete_gov_annual_attr"),
    url(r'^gov_annual_attr/add/$', add_gov_annual_attr, name='add_gov_annual_attr'),

    url(r'^save_checklist/$', save_checklist, name='save_checklist'),
]
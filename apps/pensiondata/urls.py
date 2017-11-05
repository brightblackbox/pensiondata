from django.conf.urls import url

from .views import edit_plan_annual_attr, delete_plan_annual_attr, add_plan_annual_attr, save_checklist


app_name = 'pensiondata'

urlpatterns = [

    url(r'^plan_annual_attr/edit/$', edit_plan_annual_attr, name="edit_plan_annual_attr"),
    url(r'^plan_annual_attr/delete/$', delete_plan_annual_attr, name="delete_plan_annual_attr"),
    url(r'^plan_annual_attr/add/$', add_plan_annual_attr, name='add_plan_annual_attr'),

    url(r'^plan_annual_attr/save_checklist/$', save_checklist, name='save_checklist'),
]
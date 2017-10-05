from django.conf.urls import url

from .views import edit_plan_annual_attr, delete_plan_annual_attr

urlpatterns = [

    url(r'^plan_annual_attr/edit/$', edit_plan_annual_attr, name="edit_plan_attr"),
    url(r'^plan_annual_attr/delete/$', delete_plan_annual_attr, name="delete_plan_attr"),
]
from django.conf.urls import url

from .views import edit_plan_annual_attr, delete_plan_annual_attr, add_plan_annual_attr, save_checklist, \
                    edit_gov_annual_attr, delete_gov_annual_attr, add_gov_annual_attr,plan_calculated_status, \
                    get_calculated_task_status, api_map_contribs, api_map_liabilities, api_map_search, api_chart_contribs


app_name = 'pensiondata'

urlpatterns = [

    url(r'^plan_annual_attr/edit/$', edit_plan_annual_attr, name="edit_plan_annual_attr"),
    url(r'^plan_annual_attr/delete/$', delete_plan_annual_attr, name="delete_plan_annual_attr"),
    url(r'^plan_annual_attr/add/$', add_plan_annual_attr, name='add_plan_annual_attr'),

    url(r'^gov_annual_attr/edit/$', edit_gov_annual_attr, name="edit_gov_annual_attr"),
    url(r'^gov_annual_attr/delete/$', delete_gov_annual_attr, name="delete_gov_annual_attr"),
    url(r'^gov_annual_attr/add/$', add_gov_annual_attr, name='add_gov_annual_attr'),

    url(r'^save_checklist/$', save_checklist, name='save_checklist'),
    url(r'^plan_calculated_status/$', plan_calculated_status, name='plan_calculated_status'),
    url(r'^get_calculated_task_status/$', get_calculated_task_status, name='get_calculated_task_status'),

    url(r'^api/map/search/(?P<state>[A-Za-z]{2})/$', api_map_search, name='api_map_search'),
    url(r'^api/map/contribs/(?P<state>[A-Za-z]{2})/$', api_map_contribs, name='api_map_contribs'),
    url(r'^api/map/liabilities/(?P<state>[A-Za-z]{2})/$', api_map_liabilities, name='api_map_liabilities'),
    url(r'^api/chart/contribs/(?P<government_id>\d+)/$', api_chart_contribs, name = 'api_chart_contribs'),

]
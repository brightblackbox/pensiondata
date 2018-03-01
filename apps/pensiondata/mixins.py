import json
import os
import pandas as pd
import xlrd

from django.conf import settings
from django.conf.urls import url
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.core.files.storage import default_storage

from apps.common.tmp_storages import TempFolderStorage
from .forms import ImportForm
from .tasks import import_to_database, import_reason
from celery.result import AsyncResult
from pensiondata.forms import IMPORT_FILE_FORMAT_CHOICES, IMPORT_SOURCE

try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text

from django.utils.translation import ugettext_lazy as _


SKIP_ADMIN_LOG = getattr(settings, 'IMPORT_EXPORT_SKIP_ADMIN_LOG', False)
TMP_STORAGE_CLASS = getattr(settings, 'IMPORT_EXPORT_TMP_STORAGE_CLASS',
                            TempFolderStorage)


class ImportMixinBase(object):
    def get_model_info(self):
        app_label = self.model._meta.app_label
        try:
            return ( app_label, self.model._meta.model_name, )
        except AttributeError:
            return ( app_label, self.model._meta.module_name, )

    def get_model_name(self):
        return self.model._meta.model_name


class ImportMixin(ImportMixinBase):
    """
    Import mixin.
    """

    #: template for change_list view
    change_list_template = 'admin/change_list_import.html'

    #: template for import view
    import_template_name = 'admin/import.html'

    #: import data encoding
    from_encoding = "utf-8"
    skip_admin_log = None

    # storage class for saving temporary files
    tmp_storage_class = None

    def get_skip_admin_log(self):
        if self.skip_admin_log is None:
            return SKIP_ADMIN_LOG
        else:
            return self.skip_admin_log

    def get_tmp_storage_class(self):
        if self.tmp_storage_class is None:
            return TMP_STORAGE_CLASS
        else:
            return self.tmp_storage_class

    def get_urls(self):
        urls = super(ImportMixin, self).get_urls()
        info = self.get_model_info()
        my_urls = [

            url(r'^import/$',
                self.admin_site.admin_view(self.import_action),
                name='%s_%s_import' % info),
            url(r'^get_import_progress/$',
                self.admin_site.admin_view(self.get_import_progress),
                name='%s_%s_get_import_progress' % info),
        ]
        return my_urls + urls



    def import_action(self, request, *args, **kwargs):
        '''
        Perform a dry_run of the import to make sure the import will not
        result in errors.  If there where no error, save the user
        uploaded file to a local temp file that will be used by
        'process_import' for the actual import.
        '''

        context = {}

        form = ImportForm(request.POST or None,
                          request.FILES or None)

        def get_df_documentation(xl):
            if "Documentation" in xl.sheet_names:
                df_documentation = xl.parse("Documentation")
                return df_documentation

        def get_all_sheets(list_unique_sheet_name, xl):
            dict_all_sheets = {}
            for sheet in list_unique_sheet_name:
                df_sheet = xl.parse(sheet)
                # print(df_sheet)
                dict_all_sheets[sheet] = df_sheet.to_json(orient='index')
            return dict_all_sheets

        if request.POST and form.is_valid():  # NOTE: AJAX POST
            input_format = form.cleaned_data['input_format']
            import_file = form.cleaned_data['import_file']
            source = form.cleaned_data['source']

            # for Data Source = Census and format = txt
            # be careful! hardcode here!
            if source == str(IMPORT_SOURCE[0][0]) and input_format == str(IMPORT_FILE_FORMAT_CHOICES[0][0]):
                # first always write the uploaded file to disk as it may be a
                # memory file or else based on settings upload handlers
                tmp_storage = self.get_tmp_storage_class()()
                data = bytes()
                for chunk in import_file.chunks():
                    data += chunk

                tmp_storage.save(data, 'rU')  # rb, rU

                # then read the file, using the proper format-specific mode
                # warning, big files may exceed memory
                try:
                    # here I had error with reading xlsx file
                    data = tmp_storage.readlines('rU')  # rb, rU using UTF8
                    total_rows = len(data)
                    if total_rows > 0:
                        import_task = import_to_database.delay(data, self.get_model_name())
                        resp_msg = {
                            'result': 'success',
                            'data_source': 'Census',
                            'message': 'The uploading is in progress',
                            'task_id': import_task.id,
                            'job_count': total_rows
                        }
                    else:
                        resp_msg = {
                            'result': 'empty',
                            'message': 'Empty file'
                        }
                    return JsonResponse(resp_msg)
                # except UnicodeDecodeError as e:
                #
                #     return HttpResponse(_(u"<h1>Imported file has a wrong encoding: %s</h1>" % e))
                except Exception as e:
                    print(e)
                    return JsonResponse({
                        'result': 'fail',
                        'message': _(u"%s encountered while trying to read file: %s" % (type(e).__name__, import_file.name))
                    })
            elif source == str(IMPORT_SOURCE[1][0]) and input_format == str(IMPORT_FILE_FORMAT_CHOICES[1][0]):
                tmp_storage = self.get_tmp_storage_class()()
                data = bytes()
                for chunk in import_file.chunks():
                    data += chunk
                tmp_storage.save(data, 'rb')  # rb, rU
                data = tmp_storage.read('rb')  # rb, rU using

                # "dynamically" read xlsx from tmp_storage
                workbook = xlrd.open_workbook(file_contents=data)
                xl = pd.ExcelFile(workbook, engine="xlrd")

                # get json serializer data from sheet "Documentation"
                df_documentation = get_df_documentation(xl)
                list_unique_sheet_name = list(df_documentation["Sheet"].unique())
                df_documentation = df_documentation.to_json(orient='index')

                # get all another important data from xlsx file
                dict_all_sheets = get_all_sheets(list_unique_sheet_name, xl)

                result = import_reason.delay(dict_all_sheets, df_documentation, list_unique_sheet_name)
                if result:
                    resp_msg = {
                        'result': 'success',
                        'data_source': 'Reason',
                        'message': 'The uploading is in progress',
                        'task_id': result.id,
                        'job_count': len(list_unique_sheet_name),
                    }
                else:
                    resp_msg = {
                        'result': 'empty',
                        'message': 'Downloading and parsing is done!'
                    }
                return JsonResponse(resp_msg)
            else:
                resp_msg = {
                    'result': 'fail',
                    'message': 'Not correct combination of Data Source and Format! Census - txt, Reason - xlsx'
                }
                return JsonResponse(resp_msg)
        context['title'] = _("Import")
        context['form'] = form
        context['opts'] = self.model._meta

        request.current_app = self.admin_site.name
        return TemplateResponse(request, [self.import_template_name],
                                context)

    def get_import_progress(self, request, *args, **kwargs):
        """ A view to track celery task's state """
        data = {}

        if request.is_ajax():
            if 'task_id' in request.POST.keys() and request.POST['task_id']:
                task_id = request.POST['task_id']
                import_task = AsyncResult(task_id)

                data['result'] = import_task.result or import_task.status

            else:
                data['result'] = 'No task_id in the request'
        else:
            data['result'] = 'This is not an ajax request'

        json_data = json.dumps(data)
        # return JsonResponse(json_data)
        return HttpResponse(json_data, content_type='application/json')
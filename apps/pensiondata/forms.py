from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import DataSource

IMPORT_FILE_FORMAT_CHOICES = (
    # (0, '---'),
    (1, _("txt")),
    # (2, _("csv")),
    (3, _("xlsx"))
)

IMPORT_SOURCE = (
    # (0, '---'),
    (1, _("Census")),
    # (2, _("Pension Plan Data")),
    (3, _("Reason"))
)


class ImportForm(forms.Form):
    import_file = forms.FileField(
        label=_('File to import'),
        help_text='Max Size: 5MB'
        )
    source = forms.ChoiceField(
        label=_('Data Source'),
        choices=IMPORT_SOURCE
    )
    input_format = forms.ChoiceField(
        label=_('Format'),
        choices=IMPORT_FILE_FORMAT_CHOICES,
    )

    # def __init__(self, *args, **kwargs):
    #     super(ImportForm, self).__init__(*args, **kwargs)
    #
    #     choices = [(s.pk, s.name) for s in DataSource.objects.all()]
    #
    #     choices.insert(0, ('', '---'))
    #
    #     self.fields['source'].choices = choices

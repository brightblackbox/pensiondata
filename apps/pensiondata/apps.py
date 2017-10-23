from django.apps import AppConfig


class PensiondataConfig(AppConfig):
    name = 'pensiondata'

    def ready(self):
        import pensiondata.signals
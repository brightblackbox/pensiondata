from django.core.management.base import BaseCommand, CommandError
from django.db import connection

class Command(BaseCommand):
    help = "Executes the stored procedure to update plan_annual_master_attribute"

    def handle(self, *args, **options):

        SPROC_NAME = 'update_plan_annual_master_attribute'

        cursor = connection.cursor()

        try:
            self.stdout.write('Executing stored procedure %s' % SPROC_NAME)
            cursor.callproc(SPROC_NAME)

        except:
            raise CommandError('Error executing stored procedure %s' % SPROC_NAME)

        finally:
            cursor.close()
from django.core.management.base import BaseCommand
from employees.models import Employee, Department, Position
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Удаляет все профили сотрудников, должности и подразделения'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительное удаление без подтверждения',
        )

    def handle(self, *args, **options):
        if not options['force']:
            confirm = input('Вы уверены, что хотите удалить ВСЕ данные? Это действие нельзя отменить! (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Операция отменена'))
                return

        try:
            # Удаляем всех сотрудников
            employee_count = Employee.objects.count()
            Employee.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Удалено сотрудников: {employee_count}'))

            # Удаляем все должности
            position_count = Position.objects.count()
            Position.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Удалено должностей: {position_count}'))

            # Удаляем все подразделения
            department_count = Department.objects.count()
            Department.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Удалено подразделений: {department_count}'))

            logger.info(f'Удалены все данные: {employee_count} сотрудников, {position_count} должностей, {department_count} подразделений')
            
        except Exception as e:
            logger.error(f'Ошибка при удалении данных: {str(e)}')
            self.stdout.write(self.style.ERROR(f'Произошла ошибка: {str(e)}')) 
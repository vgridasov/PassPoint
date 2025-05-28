from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Employee, Department, Position
from .resources import EmployeeResource, DepartmentResource, PositionResource
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
import csv
from io import TextIOWrapper
import logging

logger = logging.getLogger(__name__)

@admin.register(Employee)
class EmployeeAdmin(ImportExportModelAdmin):
    resource_class = EmployeeResource
    list_display = ('last_name', 'first_name', 'middle_name', 'department', 'position', 'is_fired', 'has_pass', 'lost_pass')
    list_filter = ('department', 'position', 'is_fired', 'has_pass', 'lost_pass')
    search_fields = ('last_name', 'first_name', 'middle_name')
    change_list_template = 'admin/import_export/change_list_import_export.html'

    def is_fired(self, obj):
        return obj.is_fired
    is_fired.boolean = True
    is_fired.short_description = 'Уволен'

    def has_pass(self, obj):
        return obj.has_pass
    has_pass.boolean = True
    has_pass.short_description = 'Выдан пропуск'

    def lost_pass(self, obj):
        return obj.lost_pass
    lost_pass.boolean = True
    lost_pass.short_description = 'Утерян пропуск'

    def import_action(self, request, *args, **kwargs):
        logger.info(f"Начало импорта сотрудников. Пользователь: {request.user}")
        return super().import_action(request, *args, **kwargs)

@admin.register(Department)
class DepartmentAdmin(ImportExportModelAdmin):
    resource_class = DepartmentResource
    list_display = ('name', 'full_name')
    change_list_template = 'admin/department_changelist.html'
    search_fields = ('name',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='import_departments_csv'),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        if request.method == 'POST' and request.FILES.get('csv_file'):
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                logger.warning(f"Попытка импорта неверного формата: {csv_file.name}")
                self.message_user(request, 'Файл должен быть в формате CSV', messages.ERROR)
                return redirect('..')
            
            try:
                logger.info(f"Начало импорта подразделений из файла: {csv_file.name}")
                decoded_file = TextIOWrapper(csv_file, encoding='utf-8')
                reader = csv.reader(decoded_file)
                count = 0
                for row in reader:
                    full_name = row[0].strip()
                    if full_name:
                        dept, created = Department.objects.get_or_create(
                            name=full_name,
                            defaults={'full_name': full_name}
                        )
                        if created:
                            logger.info(f"Создано новое подразделение: {dept}")
                        else:
                            logger.info(f"Использовано существующее подразделение: {dept}")
                        count += 1
                logger.info(f"Импортировано подразделений: {count}")
                self.message_user(request, f'Импортировано подразделений: {count}', messages.SUCCESS)
            except Exception as e:
                logger.error(f"Ошибка при импорте подразделений: {str(e)}")
                self.message_user(request, f'Ошибка при импорте: {str(e)}', messages.ERROR)
            return redirect('..')
        return render(request, 'admin/import_csv.html', {
            'title': 'Загрузить подразделения из CSV',
            'opts': self.model._meta,
        })

@admin.register(Position)
class PositionAdmin(ImportExportModelAdmin):
    resource_class = PositionResource
    list_display = ('name', 'full_name')
    change_list_template = 'admin/position_changelist.html'
    search_fields = ('name',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='import_positions_csv'),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        if request.method == 'POST' and request.FILES.get('csv_file'):
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                logger.warning(f"Попытка импорта неверного формата: {csv_file.name}")
                self.message_user(request, 'Файл должен быть в формате CSV', messages.ERROR)
                return redirect('..')
            
            try:
                logger.info(f"Начало импорта должностей из файла: {csv_file.name}")
                decoded_file = TextIOWrapper(csv_file, encoding='utf-8')
                reader = csv.reader(decoded_file)
                count = 0
                for row in reader:
                    full_name = row[0].strip()
                    if full_name:
                        pos, created = Position.objects.get_or_create(
                            name=full_name,
                            defaults={'full_name': full_name}
                        )
                        if created:
                            logger.info(f"Создана новая должность: {pos}")
                        else:
                            logger.info(f"Использована существующая должность: {pos}")
                        count += 1
                logger.info(f"Импортировано должностей: {count}")
                self.message_user(request, f'Импортировано должностей: {count}', messages.SUCCESS)
            except Exception as e:
                logger.error(f"Ошибка при импорте должностей: {str(e)}")
                self.message_user(request, f'Ошибка при импорте: {str(e)}', messages.ERROR)
            return redirect('..')
        return render(request, 'admin/import_csv.html', {
            'title': 'Загрузить должности из CSV',
            'opts': self.model._meta,
        })

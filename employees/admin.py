from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Employee, Department, Position
from .resources import EmployeeResource, DepartmentResource, PositionResource
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
import csv
from io import TextIOWrapper

@admin.register(Employee)
class EmployeeAdmin(ImportExportModelAdmin):
    resource_class = EmployeeResource
    list_display = ('last_name', 'first_name', 'middle_name', 'department', 'position')
    list_filter = ('department', 'position')
    search_fields = ('last_name', 'first_name', 'middle_name')
    change_list_template = 'admin/import_export/change_list_import_export.html'

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
            decoded_file = TextIOWrapper(csv_file, encoding='utf-8')
            reader = csv.reader(decoded_file)
            count = 0
            for row in reader:
                full_name = row[0].strip()
                if full_name:
                    name = full_name[:32]
                    Department.objects.get_or_create(name=name, defaults={'full_name': full_name})
                    count += 1
            self.message_user(request, f'Импортировано подразделений: {count}', messages.SUCCESS)
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
            decoded_file = TextIOWrapper(csv_file, encoding='utf-8')
            reader = csv.reader(decoded_file)
            count = 0
            for row in reader:
                full_name = row[0].strip()
                if full_name:
                    name = full_name[:32]
                    Position.objects.get_or_create(name=name, defaults={'full_name': full_name})
                    count += 1
            self.message_user(request, f'Импортировано должностей: {count}', messages.SUCCESS)
            return redirect('..')
        return render(request, 'admin/import_csv.html', {
            'title': 'Загрузить должности из CSV',
            'opts': self.model._meta,
        })

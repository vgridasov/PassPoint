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
    search_fields = ('name',)

@admin.register(Position)
class PositionAdmin(ImportExportModelAdmin):
    resource_class = PositionResource
    list_display = ('name', 'full_name')
    search_fields = ('name',)


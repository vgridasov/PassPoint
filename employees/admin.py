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
import os
import base64
from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger(__name__)

@admin.register(Employee)
class EmployeeAdmin(ImportExportModelAdmin):
    resource_class = EmployeeResource
    list_display = ('last_name', 'first_name', 'middle_name', 'department', 'position', 'is_fired', 'has_pass', 'lost_pass')
    list_filter = ('department', 'position', 'is_fired', 'has_pass', 'lost_pass')
    search_fields = ('last_name', 'first_name', 'middle_name')
    change_list_template = 'admin/import_export/change_list_import_export.html'
    actions = ['create_passes']

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

    def create_passes(self, request, queryset):
        """Массовое создание пропусков для выбранных сотрудников"""
        success_count = 0
        error_count = 0
        
        # Чтение шаблона пропуска
        template_path = os.path.join(settings.MEDIA_ROOT, 'pass-template.svg')
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            self.message_user(request, 'Файл шаблона пропуска не найден. Пожалуйста, импортируйте шаблон.', level=messages.ERROR)
            return

        for employee in queryset:
            try:
                # Подготовка фото в base64
                photo_base64 = ''
                if employee.photo:
                    try:
                        with open(employee.photo.path, 'rb') as f:
                            photo_base64 = base64.b64encode(f.read()).decode('utf-8')
                    except Exception as e:
                        logger.error(f"Ошибка при чтении фото для {employee}: {str(e)}")
                
                # Замена плейсхолдеров
                svg_content = template.replace('{Фамилия}', employee.last_name)
                svg_content = svg_content.replace('{Имя}', employee.first_name)
                svg_content = svg_content.replace('{Отчество}', employee.middle_name)
                svg_content = svg_content.replace('{Подразделение}', str(employee.department))
                svg_content = svg_content.replace('{Должность}', str(employee.position))
                svg_content = svg_content.replace('{Фото}', f'data:image/jpeg;base64,{photo_base64}' if photo_base64 else '')
                
                # Создание директории если не существует
                pass_dir = os.path.join(settings.MEDIA_ROOT, 'pass_result')
                os.makedirs(pass_dir, exist_ok=True)
                
                # Формирование имени файла
                filename = f'pass_{employee.id}_{employee.last_name}_{employee.first_name}_{employee.middle_name}.svg'
                filepath = os.path.join(pass_dir, filename)
                
                # Сохранение файла
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                
                # Обновление ссылки в модели
                relative_path = os.path.join('pass_result', filename)
                employee.pass_svg = relative_path
                employee.has_pass = True
                employee.lost_pass = False
                employee.save()
                
                success_count += 1
                logger.info(f"Пропуск успешно создан для {employee}: {filepath}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Ошибка при создании пропуска для {employee}: {str(e)}")
        
        if success_count > 0:
            self.message_user(request, f'Успешно создано пропусков: {success_count}')
        if error_count > 0:
            self.message_user(request, f'Ошибок при создании пропусков: {error_count}', level=messages.ERROR)
    
    create_passes.short_description = "Создать пропуски для выбранных сотрудников"

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


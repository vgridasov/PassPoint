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
from django.contrib.admin import SimpleListFilter

logger = logging.getLogger(__name__)

class PassStatusFilter(SimpleListFilter):
    """Фильтр для статуса пропуска"""
    title = 'Статус пропуска'
    parameter_name = 'pass_status_filter'

    def lookups(self, request, model_admin):
        return (
            (Employee.PASS_STATUS_NONE, 'Нет пропуска'),
            (Employee.PASS_STATUS_READY, 'Пропуск готов'),
            (Employee.PASS_STATUS_ISSUED, 'Пропуск выдан'),
            (Employee.PASS_STATUS_WITHDRAWN, 'Пропуск изъят/аннулирован'),
            ('is_lost', 'Отметка об утере'),
        )

    def queryset(self, request, queryset):
        if self.value() == Employee.PASS_STATUS_NONE:
            return queryset.filter(pass_status=Employee.PASS_STATUS_NONE)
        if self.value() == Employee.PASS_STATUS_READY:
            return queryset.filter(pass_status=Employee.PASS_STATUS_READY)
        if self.value() == Employee.PASS_STATUS_ISSUED:
            return queryset.filter(pass_status=Employee.PASS_STATUS_ISSUED)
        if self.value() == Employee.PASS_STATUS_WITHDRAWN:
            return queryset.filter(pass_status=Employee.PASS_STATUS_WITHDRAWN)
        if self.value() == 'is_lost':
            return queryset.filter(lost_pass=True)
        return queryset

class NoPhotoFilter(SimpleListFilter):
    """Фильтр для сотрудников без фото"""
    title = 'Наличие фото'
    parameter_name = 'photo_status'

    def lookups(self, request, model_admin):
        return (
            ('no_photo', 'Нет фото'),
            ('has_photo', 'Есть фото'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'no_photo':
            return queryset.filter(photo__isnull=True) | queryset.filter(photo='')
        if self.value() == 'has_photo':
            return queryset.exclude(photo__isnull=True).exclude(photo='')
        return queryset

@admin.register(Employee)
class EmployeeAdmin(ImportExportModelAdmin):
    resource_class = EmployeeResource
    list_display = ('last_name', 'first_name', 'middle_name', 'department', 'position', 'get_is_fired_display', 'pass_status', 'get_lost_pass_display')
    list_filter = ('department', 'position', 'is_fired', PassStatusFilter, NoPhotoFilter)
    search_fields = ('last_name', 'first_name', 'middle_name')
    change_list_template = 'admin/import_export/change_list_import_export.html'
    actions = ['create_passes', 'mark_passes_as_issued']

    @admin.display(boolean=True, description='Уволен')
    def get_is_fired_display(self, obj):
        return obj.is_fired

    @admin.display(boolean=True, description='Утерян пропуск')
    def get_lost_pass_display(self, obj):
        return obj.lost_pass

    def create_passes(self, request, queryset):
        """Массовое создание пропусков для выбранных сотрудников"""
        success_count = 0
        error_count = 0
        skipped_photo_count = 0
        skipped_status_count = 0
        
        template_path = os.path.join(settings.MEDIA_ROOT, 'pass-template.svg')
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            self.message_user(request, 'Файл шаблона пропуска не найден. Пожалуйста, импортируйте шаблон.', level=messages.ERROR)
            return

        for employee in queryset:
            if employee.pass_status not in [Employee.PASS_STATUS_NONE, Employee.PASS_STATUS_WITHDRAWN]:
                logger.info(f"Создание пропуска для {employee} пропущено: текущий статус '{employee.get_pass_status_display()}' не позволяет создать новый.")
                skipped_status_count += 1
                continue

            try:
                if not employee.photo:
                    logger.warning(f"Пропуск пропуска для {employee}: отсутствует фото")
                    skipped_photo_count += 1
                    continue

                photo_base64 = ''
                try:
                    if hasattr(employee.photo, 'path') and employee.photo.path:
                        with open(employee.photo.path, 'rb') as f:
                            photo_base64 = base64.b64encode(f.read()).decode('utf-8')
                    elif employee.photo:
                        photo_content = employee.photo.read()
                        photo_base64 = base64.b64encode(photo_content).decode('utf-8')
                        employee.photo.seek(0)
                    else:
                        logger.error(f"Фото для {employee} не имеет пути и не может быть прочитано.")
                        skipped_photo_count += 1
                        continue
                except Exception as e:
                    logger.error(f"Ошибка при чтении фото для {employee}: {str(e)}")
                    skipped_photo_count += 1
                    continue
                
                svg_content = template.replace('{Фамилия}', employee.last_name)
                svg_content = svg_content.replace('{Имя}', employee.first_name)
                svg_content = svg_content.replace('{Отчество}', employee.middle_name or '')
                svg_content = svg_content.replace('{Подразделение}', str(employee.department))
                svg_content = svg_content.replace('{Должность}', str(employee.position))
                svg_content = svg_content.replace('{Фото}', f'data:image/jpeg;base64,{photo_base64}')
                
                pass_dir = os.path.join(settings.MEDIA_ROOT, 'pass_result')
                os.makedirs(pass_dir, exist_ok=True)
                
                filename = f'pass_{employee.id}_{employee.last_name}_{employee.first_name}_{employee.middle_name or ""}.svg'
                filename = "".join(c if c.isalnum() or c in ['.', '_'] else '_' for c in filename)
                filepath = os.path.join(pass_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                
                relative_path = os.path.join('pass_result', filename)
                employee.pass_svg = relative_path
                employee.pass_status = Employee.PASS_STATUS_READY
                employee.save()
                
                success_count += 1
                logger.info(f"Пропуск успешно создан для {employee}: {filepath}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Ошибка при создании пропуска для {employee}: {str(e)}")
        
        if success_count > 0:
            self.message_user(request, f'Успешно создано пропусков: {success_count}')
        if skipped_photo_count > 0:
            self.message_user(request, f'Пропущено сотрудников (без фото): {skipped_photo_count}', level=messages.WARNING)
        if skipped_status_count > 0:
            self.message_user(request, f'Пропущено сотрудников (неверный статус пропуска): {skipped_status_count}', level=messages.WARNING)
        if error_count > 0:
            self.message_user(request, f'Ошибок при создании пропусков: {error_count}', level=messages.ERROR)
    
    create_passes.short_description = "Создать пропуски для выбранных сотрудников"

    def mark_passes_as_issued(self, request, queryset):
        """Установить статус пропуска 'Выдан' для выбранных сотрудников"""
        updated = queryset.update(pass_status=Employee.PASS_STATUS_ISSUED)
        self.message_user(request, f'Статус пропуска "Выдан" установлен для {updated} сотрудников')
    mark_passes_as_issued.short_description = "Установить статус пропуска 'Выдан'"

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


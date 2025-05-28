import os
import shutil
import logging
from django.conf import settings
from import_export import resources
from .models import Employee, Department, Position
from django.contrib.auth.models import User
from import_export.results import RowResult

logger = logging.getLogger(__name__)

class EmployeeResource(resources.ModelResource):
    class Meta:
        model = Employee
        fields = ('id', 'last_name', 'first_name', 'middle_name', 'department', 'position', 'photo', 'pass_svg')
        export_order = ('id', 'last_name', 'first_name', 'middle_name', 'department', 'position', 'photo', 'pass_svg')

    def before_import_row(self, row, row_number=None, **kwargs):
        logger.info(f"Импорт строки {row_number}: {row}")
        # Подразделение
        dep_val = row.get('department') or row.get('department__name')
        if dep_val:
            dep_val = str(dep_val).strip()
            if dep_val.isdigit():
                try:
                    dep = Department.objects.get(pk=int(dep_val))
                    logger.info(f"Найдено подразделение по ID: {dep}")
                except Department.DoesNotExist:
                    logger.error(f"Подразделение с id={dep_val} не найдено")
                    raise Exception(f"Строка {row_number or ''}: подразделение с id={dep_val} не найдено")
            else:
                dep, created = Department.objects.get_or_create(
                    name=dep_val,
                    defaults={'full_name': dep_val}
                )
                if created:
                    logger.info(f"Создано новое подразделение: {dep}")
                else:
                    logger.info(f"Использовано существующее подразделение: {dep}")
            row['department'] = dep.pk
        # Должность
        pos_val = row.get('position') or row.get('position__name')
        if pos_val:
            pos_val = str(pos_val).strip()
            if pos_val.isdigit():
                try:
                    pos = Position.objects.get(pk=int(pos_val))
                    logger.info(f"Найдена должность по ID: {pos}")
                except Position.DoesNotExist:
                    logger.error(f"Должность с id={pos_val} не найдена")
                    raise Exception(f"Строка {row_number or ''}: должность с id={pos_val} не найдена")
            else:
                pos, created = Position.objects.get_or_create(
                    name=pos_val,
                    defaults={'full_name': pos_val}
                )
                if created:
                    logger.info(f"Создана новая должность: {pos}")
                else:
                    logger.info(f"Использована существующая должность: {pos}")
            row['position'] = pos.pk
        # Фото
        photo_path = row.get('photo')
        if photo_path:
            photo_path = str(photo_path).replace('\\', '/').replace('\\', '/')
            if not photo_path.startswith('employee_photos/'):
                src_path = os.path.join(settings.BASE_DIR, photo_path)
                if os.path.exists(src_path):
                    dst_dir = os.path.join(settings.MEDIA_ROOT, 'employee_photos')
                    os.makedirs(dst_dir, exist_ok=True)
                    dst_path = os.path.join(dst_dir, os.path.basename(photo_path))
                    shutil.copy2(src_path, dst_path)
                    row['photo'] = f'employee_photos/{os.path.basename(photo_path)}'
                    logger.info(f"Скопировано фото: {src_path} -> {dst_path}")
                else:
                    logger.warning(f"Файл фото не найден: {src_path}")
                    row['photo'] = ''
            else:
                logger.info(f"Использовано существующее фото: {photo_path}")
                row['photo'] = photo_path

    def after_import_row(self, row, row_result, row_number=None, **kwargs):
        if row_result.import_type == RowResult.IMPORT_TYPE_NEW:
            logger.info(f"Создан новый сотрудник: {row.get('last_name')} {row.get('first_name')}")
        elif row_result.import_type == RowResult.IMPORT_TYPE_UPDATE:
            logger.info(f"Обновлен сотрудник: {row.get('last_name')} {row.get('first_name')}")

class DepartmentResource(resources.ModelResource):
    class Meta:
        model = Department
        fields = ('id', 'name', 'full_name')
        export_order = ('id', 'name', 'full_name')

    def before_import_row(self, row, **kwargs):
        logger.info(f"Импорт подразделения: {row}")
        if row.get('name'):
            row['full_name'] = row['name']

    def after_import_row(self, row, row_result, **kwargs):
        if row_result.import_type == RowResult.IMPORT_TYPE_NEW:
            logger.info(f"Создано новое подразделение: {row.get('name')}")
        elif row_result.import_type == RowResult.IMPORT_TYPE_UPDATE:
            logger.info(f"Обновлено подразделение: {row.get('name')}")

class PositionResource(resources.ModelResource):
    class Meta:
        model = Position
        fields = ('id', 'name', 'full_name')
        export_order = ('id', 'name', 'full_name')

    def before_import_row(self, row, **kwargs):
        logger.info(f"Импорт должности: {row}")
        if row.get('name'):
            row['full_name'] = row['name']

    def after_import_row(self, row, row_result, **kwargs):
        if row_result.import_type == RowResult.IMPORT_TYPE_NEW:
            logger.info(f"Создана новая должность: {row.get('name')}")
        elif row_result.import_type == RowResult.IMPORT_TYPE_UPDATE:
            logger.info(f"Обновлена должность: {row.get('name')}") 
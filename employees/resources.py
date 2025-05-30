import os
import shutil
import logging
from django.conf import settings
from import_export import resources
from .models import Employee, Department, Position
from django.contrib.auth.models import User
from import_export.results import RowResult
from import_export.fields import Field

logger = logging.getLogger(__name__)

class EmployeeResource(resources.ModelResource):
    # Добавляем поля для экспорта
    department = Field(attribute='department', column_name='department')
    position = Field(attribute='position', column_name='position')
    lost_pass = Field(attribute='lost_pass', column_name='lost_pass')

    # Сопоставление русских заголовков с полями модели
    RUSSIAN_FIELD_MAP = {
        'Фамилия': 'last_name',
        'Имя': 'first_name',
        'Отчество': 'middle_name',
        'Подразделение': 'department',
        'Должность': 'position',
        'Пропуск': 'has_pass',
        'Уволен': 'is_fired',
    }

    class Meta:
        model = Employee
        fields = ('id', 'last_name', 'first_name', 'middle_name', 'department', 'position', 'photo', 'pass_svg', 'is_fired', 'has_pass')
        export_order = ('id', 'last_name', 'first_name', 'middle_name', 'department', 'position', 'photo', 'pass_svg', 'is_fired', 'has_pass', 'lost_pass')

    def import_row(self, row, instance_loader, **kwargs):
        # Сопоставляем русские заголовки с полями модели
        for ru, en in self.RUSSIAN_FIELD_MAP.items():
            if ru in row and en not in row:
                row[en] = row[ru]
        return super().import_row(row, instance_loader, **kwargs)

    def before_import_row(self, row, **kwargs):
        """Обработка данных перед импортом"""
        logger.info(f"Импорт сотрудника: {row}")
        
        # Очищаем строковые поля от лишних пробелов
        for field in ['last_name', 'first_name', 'middle_name', 'department', 'position']:
            if field in row and row[field]:
                row[field] = row[field].strip()
        
        # Проверяем наличие обязательных полей
        if not all(row.get(field) for field in ['last_name', 'first_name', 'department', 'position']):
            logger.error("Отсутствуют обязательные поля")
            return
        
        # Обработка подразделения
        dep_val = row.get('department', '').strip()
        if not dep_val:
            logger.error("Пустое значение подразделения")
            return
            
        try:
            if dep_val.isdigit():
                dep = Department.objects.get(pk=int(dep_val))
            else:
                dep, created = Department.objects.get_or_create(
                    name=dep_val,
                    defaults={'full_name': dep_val}
                )
                if created:
                    logger.info(f"Создано новое подразделение: {dep.name}")
                else:
                    logger.info(f"Найдено существующее подразделение: {dep.name}")
            # Устанавливаем значение в row
            row['department'] = dep
        except Department.DoesNotExist:
            logger.error(f"Подразделение не найдено: {dep_val}")
            return
        except Exception as e:
            logger.error(f"Ошибка при обработке подразделения: {str(e)}")
            return

        # Обработка должности
        pos_val = row.get('position', '').strip()
        if not pos_val:
            logger.error("Пустое значение должности")
            return
            
        try:
            if pos_val.isdigit():
                pos = Position.objects.get(pk=int(pos_val))
            else:
                pos, created = Position.objects.get_or_create(
                    name=pos_val,
                    defaults={'full_name': pos_val}
                )
                if created:
                    logger.info(f"Создана новая должность: {pos.name}")
                else:
                    logger.info(f"Найдена существующая должность: {pos.name}")
            # Устанавливаем значение в row
            row['position'] = pos
        except Position.DoesNotExist:
            logger.error(f"Должность не найдена: {pos_val}")
            return
        except Exception as e:
            logger.error(f"Ошибка при обработке должности: {str(e)}")
            return

        # Проверяем существование сотрудника
        try:
            existing_employee = Employee.objects.filter(
                last_name=row['last_name'].strip(),
                first_name=row['first_name'].strip(),
                middle_name=row.get('middle_name', '').strip(),
                department=dep,
                position=pos
            ).first()
            
            if existing_employee:
                logger.info(f"Найден существующий сотрудник: {existing_employee}")
                # Устанавливаем ID существующего сотрудника для обновления
                row['id'] = existing_employee.id
                # Обновляем только непустые поля
                for field in ['photo', 'pass_svg', 'is_fired', 'has_pass']:
                    if field in row and row[field] and row[field].strip():
                        setattr(existing_employee, field, row[field].strip())
                existing_employee.save()
                
        except Exception as e:
            logger.error(f"Ошибка при проверке существующего сотрудника: {str(e)}")
            return

        # Обработка фотографии
        if row.get('photo'):
            photo_path = row['photo'].strip()
            if not photo_path:
                return
                
            src_path = os.path.join(settings.MEDIA_ROOT, photo_path)
            if os.path.exists(src_path):
                try:
                    if not photo_path.startswith('employee_photos/'):
                        dst_dir = os.path.join(settings.MEDIA_ROOT, 'employee_photos')
                        os.makedirs(dst_dir, exist_ok=True)
                        dst_path = os.path.join(dst_dir, os.path.basename(photo_path))
                        shutil.copy2(src_path, dst_path)
                        row['photo'] = f'employee_photos/{os.path.basename(photo_path)}'
                        logger.info(f"Скопирована фотография: {row['photo']}")
                except Exception as e:
                    logger.error(f"Ошибка при копировании фотографии: {str(e)}")
                    return
            else:
                logger.error(f"Файл фотографии не найден: {src_path}")
                return

    def after_import_row(self, row, row_result, **kwargs):
        """Обработка после импорта строки"""
        if row_result.import_type == row_result.IMPORT_TYPE_NEW:
            logger.info(f"Создан новый сотрудник: {row}")
        elif row_result.import_type == row_result.IMPORT_TYPE_UPDATE:
            logger.info(f"Обновлен существующий сотрудник: {row}")

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
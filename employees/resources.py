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

class ImportValidationError(Exception):
    """Кастомное исключение для валидации импорта"""
    pass

class EmployeeResource(resources.ModelResource):
    # Добавляем поля для экспорта
    department = Field(attribute='department', column_name='department')
    position = Field(attribute='position', column_name='position')
    lost_pass = Field(attribute='lost_pass', column_name='lost_pass')
    pass_status_display = Field(attribute='get_pass_status_display', column_name='Статус пропуска')

    # Сопоставление русских заголовков с полями модели
    RUSSIAN_FIELD_MAP = {
        'Фамилия': 'last_name',
        'Имя': 'first_name',
        'Отчество': 'middle_name',
        'Подразделение': 'department',
        'Должность': 'position',
        'Статус пропуска': 'pass_status',
        'Уволен': 'is_fired',
    }

    class Meta:
        model = Employee
        fields = ('id', 'last_name', 'first_name', 'middle_name', 'department', 'position', 'photo', 'pass_svg', 'is_fired', 'pass_status', 'lost_pass')
        export_order = ('id', 'last_name', 'first_name', 'middle_name', 'department', 'position', 'photo', 'pass_svg', 'is_fired', 'pass_status', 'lost_pass')

    def before_import_row(self, row, **kwargs):
        """Обработка перед импортом строки"""
        # Создаем словарь для сопоставления русских названий полей
        field_mapping = {
            'Фамилия': 'last_name',
            'Имя': 'first_name',
            'Отчество': 'middle_name',
            'Подразделение': 'department',
            'Должность': 'position',
            'Статус пропуска': 'pass_status',
            'Уволен': 'is_fired',
            'Утерян пропуск': 'lost_pass',
            'Фото': 'photo'
        }

        # Преобразуем русские названия полей в английские
        new_row = {}
        for key, value in row.items():
            if key in field_mapping:
                new_row[field_mapping[key]] = value
            else:
                new_row[key] = value

        # Очистка строковых полей
        for field in ['last_name', 'first_name', 'middle_name', 'department', 'position']:
            if field in new_row:
                new_row[field] = new_row[field].strip() if new_row[field] else ''

        # Проверка обязательных полей
        required_fields = ['last_name', 'first_name', 'department', 'position']
        for field in required_fields:
            if not new_row.get(field):
                logger.error(f"Отсутствует обязательное поле: {field}")
                raise ImportValidationError(f"Отсутствует обязательное поле: {field}")

        # Обработка подразделения
        department_value = new_row['department']
        try:
            if str(department_value).isdigit():
                department = Department.objects.get(id=department_value)
            else:
                department, created = Department.objects.get_or_create(
                    name=department_value,
                    defaults={'full_name': department_value}
                )
                if created:
                    logger.info(f"Создано новое подразделение: {department_value}")
            new_row['department'] = department
        except Department.DoesNotExist:
            logger.error(f"Подразделение не найдено: {department_value}")
            raise ImportValidationError(f"Подразделение не найдено: {department_value}")

        # Обработка должности
        position_value = new_row['position']
        try:
            if str(position_value).isdigit():
                position = Position.objects.get(id=position_value)
            else:
                position, created = Position.objects.get_or_create(
                    name=position_value,
                    defaults={'full_name': position_value}
                )
                if created:
                    logger.info(f"Создана новая должность: {position_value}")
            new_row['position'] = position
        except Position.DoesNotExist:
            logger.error(f"Должность не найдена: {position_value}")
            raise ImportValidationError(f"Должность не найдена: {position_value}")

        # Проверка существующего сотрудника
        existing_employees = Employee.objects.filter(
            last_name=new_row['last_name'],
            first_name=new_row['first_name'],
            middle_name=new_row.get('middle_name', ''),
            department=department
        )
        
        if existing_employees.exists():
            # Логируем все найденные дубликаты
            for emp in existing_employees:
                logger.warning(
                    f"Найден дубликат сотрудника: {emp} "
                    f"(ID: {emp.id}, Должность: {emp.position}, "
                    f"Статус пропуска: {emp.get_pass_status_display()})"
                )
            logger.info(f"Пропуск импорта: сотрудник уже существует: {new_row['last_name']} {new_row['first_name']} {new_row.get('middle_name', '')}")
            raise ImportValidationError("Сотрудник уже существует")

        # Обработка фотографии
        if new_row.get('photo'):
            photo_path = new_row['photo'].strip()
            if not photo_path:
                raise ImportValidationError("Пустой путь к фотографии")

            # Проверяем существование файла
            src_path = os.path.join(settings.MEDIA_ROOT, photo_path)
            if not os.path.exists(src_path):
                logger.error(f"Файл фотографии не найден: {src_path}")
                raise ImportValidationError(f"Файл фотографии не найден: {photo_path}")

            try:
                if not photo_path.startswith('employee_photos/'):
                    dst_dir = os.path.join(settings.MEDIA_ROOT, 'employee_photos')
                    os.makedirs(dst_dir, exist_ok=True)
                    
                    # Получаем имя файла и обрабатываем пробелы
                    filename = os.path.basename(photo_path)
                    # Заменяем пробелы на подчеркивания
                    safe_filename = filename.replace(' ', '_')
                    # Если имя файла изменилось, логируем это
                    if safe_filename != filename:
                        logger.info(f"Имя файла изменено с '{filename}' на '{safe_filename}' для избежания проблем с пробелами")
                    
                    dst_path = os.path.join(dst_dir, safe_filename)
                    shutil.copy2(src_path, dst_path)
                    new_row['photo'] = f'employee_photos/{safe_filename}'
                    logger.info(f"Скопирована фотография: {new_row['photo']}")
            except Exception as e:
                logger.error(f"Ошибка при копировании фотографии: {str(e)}")
                raise ImportValidationError(f"Ошибка при копировании фотографии: {str(e)}")

        # Обработка статуса пропуска
        if 'pass_status' in new_row:
            status_map = {
                'Нет': 'none',
                'Готов': 'ready',
                'Выдан': 'issued',
                'Изъят': 'withdrawn',
                'Изъят/Аннулирован': 'withdrawn'
            }
            new_row['pass_status'] = status_map.get(new_row['pass_status'], 'none')

        # Обновляем исходный row новыми значениями
        row.clear()
        row.update(new_row)

    def after_import_row(self, row, row_result, **kwargs):
        """Обработка после импорта строки"""
        if row_result.import_type == row_result.IMPORT_TYPE_NEW:
            logger.info(f"Создан новый сотрудник: {row}")
        elif row_result.import_type == row_result.IMPORT_TYPE_UPDATE:
            logger.info(f"Обновлен существующий сотрудник: {row}")

    def import_row(self, row, instance_loader, **kwargs):
        """Переопределяем метод импорта для обработки ошибок"""
        try:
            return super().import_row(row, instance_loader, **kwargs)
        except ImportValidationError as e:
            # Логируем ошибку и пропускаем строку
            logger.error(f"Ошибка валидации при импорте: {str(e)}")
            # Возвращаем RowResult с ошибкой, но не прерываем импорт
            return RowResult(import_type=RowResult.IMPORT_TYPE_SKIP, error=str(e))

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
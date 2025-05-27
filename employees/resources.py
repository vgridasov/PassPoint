import os
import shutil
from django.conf import settings
from import_export import resources
from .models import Employee, Department, Position
from django.contrib.auth.models import User
from import_export.results import RowResult

class EmployeeResource(resources.ModelResource):
    class Meta:
        model = Employee
        fields = ('id', 'last_name', 'first_name', 'middle_name', 'department', 'position', 'photo', 'pass_svg')
        export_order = ('id', 'last_name', 'first_name', 'middle_name', 'department', 'position', 'photo', 'pass_svg')

    def before_import_row(self, row, row_number=None, **kwargs):
        # Подразделение
        dep_val = row.get('department') or row.get('department__name')
        if dep_val:
            dep_val = str(dep_val).strip()
            if dep_val.isdigit():
                try:
                    dep = Department.objects.get(pk=int(dep_val))
                except Department.DoesNotExist:
                    raise Exception(f"Строка {row_number or ''}: подразделение с id={dep_val} не найдено")
            else:
                dep, _ = Department.objects.get_or_create(name=dep_val, defaults={'full_name': dep_val})
            row['department'] = dep.pk
        # Должность
        pos_val = row.get('position') or row.get('position__name')
        if pos_val:
            pos_val = str(pos_val).strip()
            if pos_val.isdigit():
                try:
                    pos = Position.objects.get(pk=int(pos_val))
                except Position.DoesNotExist:
                    raise Exception(f"Строка {row_number or ''}: должность с id={pos_val} не найдена")
            else:
                pos, _ = Position.objects.get_or_create(name=pos_val, defaults={'full_name': pos_val})
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
                else:
                    row['photo'] = ''
            else:
                row['photo'] = photo_path

class DepartmentResource(resources.ModelResource):
    class Meta:
        model = Department
        fields = ('id', 'name', 'full_name')
        export_order = ('id', 'name', 'full_name')

    def before_import_row(self, row, **kwargs):
        if not row.get('full_name') and row.get('name'):
            row['full_name'] = row['name']

class PositionResource(resources.ModelResource):
    class Meta:
        model = Position
        fields = ('id', 'name', 'full_name')
        export_order = ('id', 'name', 'full_name')

    def before_import_row(self, row, **kwargs):
        if not row.get('full_name') and row.get('name'):
            row['full_name'] = row['name'] 
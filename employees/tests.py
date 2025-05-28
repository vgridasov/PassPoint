import pytest
from django.test import TestCase, Client
from django.urls import reverse
from .models import Employee, Department, Position
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
import csv
import io
import os
from django.conf import settings

@pytest.mark.django_db
class EmployeeModelTest(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Test Department")
        self.position = Position.objects.create(name="Test Position")
        self.employee = Employee.objects.create(
            first_name="Test",
            last_name="User",
            department=self.department,
            position=self.position
        )

    def test_employee_creation(self):
        self.assertEqual(self.employee.first_name, "Test")
        self.assertEqual(self.employee.last_name, "User")

@pytest.mark.django_db
class EmployeeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_employee_list_view(self):
        response = self.client.get(reverse('employee_list'))
        self.assertEqual(response.status_code, 200)

    def test_employee_detail_view(self):
        department = Department.objects.create(name="Test Department")
        position = Position.objects.create(name="Test Position")
        employee = Employee.objects.create(
            first_name="Test",
            last_name="User",
            department=department,
            position=position
        )
        response = self.client.get(reverse('employee_detail', args=[employee.id]))
        self.assertEqual(response.status_code, 200)

@pytest.mark.django_db
class ImportTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@example.com'
        )
        self.client.login(username='admin', password='admin123')
        
        # Создаем тестовые CSV файлы
        self.departments_csv = self._create_csv_file(['Отдел разработки', 'Отдел тестирования'])
        self.positions_csv = self._create_csv_file(['Разработчик', 'Тестировщик'])
        
    def _create_csv_file(self, rows):
        output = io.StringIO()
        writer = csv.writer(output)
        for row in rows:
            writer.writerow([row])
        output.seek(0)
        return SimpleUploadedFile(
            "test.csv",
            output.getvalue().encode('utf-8'),
            content_type="text/csv"
        )

    def test_department_import(self):
        response = self.client.post(
            reverse('admin:import_departments_csv'),
            {'csv_file': self.departments_csv}
        )
        self.assertEqual(response.status_code, 302)  # Редирект после успешного импорта
        
        # Проверяем созданные подразделения
        departments = Department.objects.all()
        self.assertEqual(departments.count(), 2)
        
        # Проверяем, что name и full_name совпадают
        for dept in departments:
            self.assertEqual(dept.name, dept.full_name)
            
    def test_position_import(self):
        response = self.client.post(
            reverse('admin:import_positions_csv'),
            {'csv_file': self.positions_csv}
        )
        self.assertEqual(response.status_code, 302)
        
        # Проверяем созданные должности
        positions = Position.objects.all()
        self.assertEqual(positions.count(), 2)
        
        # Проверяем, что name и full_name совпадают
        for pos in positions:
            self.assertEqual(pos.name, pos.full_name)
            
    def test_invalid_file_format(self):
        # Создаем файл с неправильным расширением
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"invalid content",
            content_type="text/plain"
        )
        
        response = self.client.post(
            reverse('admin:import_departments_csv'),
            {'csv_file': invalid_file}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Department.objects.count(), 0)
        
    def test_employee_import_with_departments(self):
        # Сначала импортируем подразделения
        self.client.post(
            reverse('admin:import_departments_csv'),
            {'csv_file': self.departments_csv}
        )
        
        # Создаем CSV для сотрудников
        employees_csv = self._create_csv_file([
            'Иванов,Иван,Иванович,Отдел разработки,Разработчик',
            'Петров,Петр,Петрович,Отдел тестирования,Тестировщик'
        ])
        
        response = self.client.post(
            reverse('admin:employees_employee_import'),
            {'csv_file': employees_csv}
        )
        self.assertEqual(response.status_code, 302)
        
        # Проверяем созданных сотрудников
        employees = Employee.objects.all()
        self.assertEqual(employees.count(), 2)
        
        # Проверяем связи с подразделениями
        for emp in employees:
            self.assertIsNotNone(emp.department)
            self.assertIsNotNone(emp.position)
            self.assertEqual(emp.department.name, emp.department.full_name)
            self.assertEqual(emp.position.name, emp.position.full_name)

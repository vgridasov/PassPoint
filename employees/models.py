from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название подразделения')
    full_name = models.CharField(max_length=255, verbose_name='Полное наименование подразделения', blank=True, help_text='Используется только в админке и при импорте')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'

class Position(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название должности')
    full_name = models.CharField(max_length=255, verbose_name='Полное наименование должности', blank=True, help_text='Используется только в админке и при импорте')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'

class Employee(models.Model):
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    middle_name = models.CharField(max_length=100, verbose_name='Отчество', blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, verbose_name='Подразделение')
    position = models.ForeignKey(Position, on_delete=models.PROTECT, verbose_name='Должность')
    photo = models.ImageField(upload_to='employee_photos/', verbose_name='Фото', blank=True)
    is_fired = models.BooleanField(default=False, verbose_name='Уволен')
    has_pass = models.BooleanField(default=False, verbose_name='Выдан пропуск')
    lost_pass = models.BooleanField(default=False, verbose_name='Утерян пропуск')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}"
    
    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

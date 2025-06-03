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
    PASS_STATUS_NONE = 'none'
    PASS_STATUS_READY = 'ready'
    PASS_STATUS_ISSUED = 'issued'
    PASS_STATUS_WITHDRAWN = 'withdrawn'

    PASS_STATUS_CHOICES = [
        (PASS_STATUS_NONE, 'Нет'),
        (PASS_STATUS_READY, 'Готов'),
        (PASS_STATUS_ISSUED, 'Выдан'),
        (PASS_STATUS_WITHDRAWN, 'Изъят/Аннулирован'),
    ]

    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    middle_name = models.CharField(max_length=100, verbose_name='Отчество', blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, verbose_name='Подразделение')
    position = models.ForeignKey(Position, on_delete=models.PROTECT, verbose_name='Должность')
    photo = models.ImageField(upload_to='employee_photos/', verbose_name='Фото', blank=True)
    is_fired = models.BooleanField(default=False, verbose_name='Уволен')
    lost_pass = models.BooleanField(default=False, verbose_name='Утерян пропуск')
    
    pass_status = models.CharField(
        max_length=10,
        choices=PASS_STATUS_CHOICES,
        default=PASS_STATUS_NONE,
        verbose_name='Статус пропуска'
    )
    pass_svg = models.FileField(upload_to='pass_result/', null=True, blank=True, verbose_name='Пропуск (SVG)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    _original_pass_status = None # Для отслеживания исходного статуса пропуска
    _original_lost_pass = None # Для отслеживания исходного состояния lost_pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Сохраняем начальные значения при инициализации существующего объекта
        if self.pk:
            self._original_pass_status = self.pass_status
            self._original_lost_pass = self.lost_pass

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        
        # Получаем предыдущее состояние объекта из БД, если он уже существует и не был загружен ранее
        # Однако, __init__ уже должен был сохранить начальные значения для существующих объектов
        # Этот блок можно упростить или удалить, если __init__ надежно отрабатывает
        old_pass_status_in_db = self._original_pass_status
        old_lost_pass_in_db = self._original_lost_pass

        if not is_new and (old_pass_status_in_db is None or old_lost_pass_in_db is None):
            # Попытка загрузить из БД, если __init__ не был вызван для существующего объекта 
            # (например, при обновлении через queryset.update(), но save() все равно вызовется для каждой модели)
            # Это маловероятно для стандартного сохранения через форму/админку, но для полноты.
            try:
                current_db_instance = Employee.objects.get(pk=self.pk)
                old_pass_status_in_db = current_db_instance.pass_status
                old_lost_pass_in_db = current_db_instance.lost_pass
            except Employee.DoesNotExist:
                pass # Оставляем None, если что-то пошло не так

        # 1. Логика при установке pass_status = 'none'
        if self.pass_status == self.PASS_STATUS_NONE and self.pass_svg:
            self.pass_svg.delete(save=False) 
            self.pass_svg = None

        # 2. Логика при изменении lost_pass на True
        # Если lost_pass стал True (был False или объект новый) И старый статус пропуска был 'issued'
        if self.lost_pass and not old_lost_pass_in_db and old_pass_status_in_db == self.PASS_STATUS_ISSUED:
            self.pass_status = self.PASS_STATUS_WITHDRAWN
        
        super().save(*args, **kwargs)

        # Обновляем _original_ значения после сохранения
        if self.pk: # Убедимся, что объект сохранен и имеет PK
            self._original_pass_status = self.pass_status
            self._original_lost_pass = self.lost_pass

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

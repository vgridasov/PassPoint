import logging
logger = logging.getLogger(__name__)

# Тестовый лог при импорте модуля
logger.info("Модуль employees.views загружен")

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Employee, Department, Position
from .forms import EmployeeForm, DepartmentForm, PositionForm
from django.core.paginator import Paginator
from django.db.models.functions import Lower
from django.db.models import Q
import os
import base64
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_superuser or user.groups.filter(name='Администратор').exists()

@login_required
def employee_list(request):
    logger.info(f"Запрос списка сотрудников. Пользователь: {request.user}")
    employees = Employee.objects.all().order_by('last_name', 'first_name')
    search_query = request.GET.get('search', '')
    if search_query:
        logger.info(f"Поиск сотрудников по запросу: {search_query}")
        employees = employees.filter(
            Q(last_name__iregex=search_query) |
            Q(first_name__iregex=search_query) |
            Q(middle_name__iregex=search_query)
        )
    
    # Если запрошен полный список
    if request.GET.get('show_all'):
        return render(request, 'employees/employee_list.html', {
            'page_obj': employees,
            'view_mode': request.GET.get('view', 'cards'),
            'search_query': search_query,
            'show_all': True
        })
    
    paginator = Paginator(employees, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'employees/employee_list.html', {
        'page_obj': page_obj, 
        'view_mode': request.GET.get('view', 'cards'),
        'search_query': search_query
    })

@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    # Проверка существования файла пропуска
    if employee.pass_svg and not os.path.exists(employee.pass_svg.path):
        employee.pass_svg = None
        employee.save()
        messages.warning(request, 'Файл пропуска не найден. Пожалуйста, создайте пропуск заново.')
    
    view_mode = request.GET.get('view', 'cards')
    return render(request, 'employees/employee_detail.html', {'employee': employee, 'view_mode': view_mode})

@user_passes_test(is_admin)
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сотрудник успешно добавлен')
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'Добавить сотрудника'})

@user_passes_test(is_admin)
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Данные сотрудника обновлены')
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'Редактировать сотрудника'})

@login_required
def department_list(request):
    departments = Department.objects.all().order_by('name')
    search_query = request.GET.get('search', '')
    if search_query:
        departments = departments.filter(name__iregex=search_query)
    
    # Если запрошен полный список
    if request.GET.get('show_all'):
        return render(request, 'employees/department_list.html', {
            'page_obj': departments,
            'search_query': search_query,
            'show_all': True
        })
    
    paginator = Paginator(departments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'employees/department_list.html', {
        'page_obj': page_obj, 
        'search_query': search_query
    })

@user_passes_test(is_admin)
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Подразделение добавлено')
            return redirect('department_list')
    else:
        form = DepartmentForm()
    return render(request, 'employees/department_form.html', {'form': form, 'title': 'Добавить подразделение'})

@login_required
def position_list(request):
    positions = Position.objects.all().order_by('name')
    search_query = request.GET.get('search', '')
    if search_query:
        positions = positions.filter(name__iregex=search_query)
    
    # Если запрошен полный список
    if request.GET.get('show_all'):
        return render(request, 'employees/position_list.html', {
            'page_obj': positions,
            'search_query': search_query,
            'show_all': True
        })
    
    paginator = Paginator(positions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'employees/position_list.html', {
        'page_obj': page_obj, 
        'search_query': search_query
    })

@user_passes_test(is_admin)
def position_create(request):
    if request.method == 'POST':
        form = PositionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Должность добавлена')
            return redirect('position_list')
    else:
        form = PositionForm()
    return render(request, 'employees/position_form.html', {'form': form, 'title': 'Добавить должность'})

@login_required
def employees_by_department(request, department_id):
    department = get_object_or_404(Department, pk=department_id)
    employees = Employee.objects.filter(department=department).order_by('last_name', 'first_name')
    paginator = Paginator(employees, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    view_mode = request.GET.get('view', 'cards')
    return render(request, 'employees/employee_list.html', {
        'page_obj': page_obj,
        'view_mode': view_mode,
        'filter_title': f'Сотрудники подразделения: {department.name}',
    })

@login_required
def employees_by_position(request, position_id):
    position = get_object_or_404(Position, pk=position_id)
    employees = Employee.objects.filter(position=position).order_by('last_name', 'first_name')
    paginator = Paginator(employees, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    view_mode = request.GET.get('view', 'cards')
    return render(request, 'employees/employee_list.html', {
        'page_obj': page_obj,
        'view_mode': view_mode,
        'filter_title': f'Сотрудники должности: {position.name}',
    })

@user_passes_test(is_admin)
@require_POST
def create_pass(request, pk):
    """Создание пропуска в формате SVG"""
    try:
        employee = Employee.objects.get(pk=pk)
        logger.info(f"Попытка создания пропуска для сотрудника {employee}")
        
        # Чтение шаблона пропуска
        template_path = os.path.join(settings.MEDIA_ROOT, 'pass-template.svg')
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            logger.warning(f"Шаблон пропуска не найден: {template_path}")
            return JsonResponse({
                'success': False,
                'need_template': True,
                'message': 'Файл шаблона пропуска не найден. Пожалуйста, импортируйте шаблон.'
            }, status=404)
        
        # Подготовка фото в base64
        photo_base64 = ''
        if employee.photo:
            try:
                with open(employee.photo.path, 'rb') as f:
                    photo_base64 = base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                logger.error(f"Ошибка при чтении фото: {str(e)}")
        
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
        employee.save()
        
        logger.info(f"Пропуск успешно создан: {filepath}")
        return JsonResponse({
            'success': True,
            'message': 'Пропуск успешно создан',
            'pass_url': employee.pass_svg.url
        })
        
    except Employee.DoesNotExist:
        logger.error(f"Сотрудник не найден: pk={pk}")
        return JsonResponse({
            'success': False,
            'message': 'Сотрудник не найден'
        }, status=404)
    except Exception as e:
        logger.error(f"Ошибка при создании пропуска: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при создании пропуска: {str(e)}'
        }, status=400)


# Этот кусок не работает!
@csrf_exempt
@require_POST
def import_pass_template(request):
    """Импорт шаблона пропуска (SVG) через POST"""
    file = request.FILES.get('templateFile')
    if not file:
        logger.warning("Попытка импорта без файла")
        return JsonResponse({'success': False, 'message': 'Файл не выбран.'}, status=400)
    if not file.name.lower().endswith('.svg'):
        logger.warning(f"Попытка импорта неверного формата: {file.name}")
        return JsonResponse({'success': False, 'message': 'Только файлы SVG поддерживаются.'}, status=400)
    try:
        # Проверяем и создаем директорию media если её нет
        if not os.path.exists(settings.MEDIA_ROOT):
            os.makedirs(settings.MEDIA_ROOT)
            logger.info(f"Создана директория media: {settings.MEDIA_ROOT}")

        # Используем FileSystemStorage для сохранения в media
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = 'pass-template.svg'
        
        # Проверяем права на запись
        if not os.access(settings.MEDIA_ROOT, os.W_OK):
            logger.error(f"Нет прав на запись в директорию: {settings.MEDIA_ROOT}")
            return JsonResponse({
                'success': False, 
                'message': 'Нет прав на запись в директорию media'
            }, status=500)

        # Удаляем старый файл если есть
        if fs.exists(filename):
            fs.delete(filename)
            logger.info(f"Удален старый шаблон: {filename}")

        # Сохраняем новый файл
        saved_name = fs.save(filename, file)
        logger.info(f"Шаблон пропуска импортирован: {saved_name}")
        
        # Проверяем что файл действительно создался
        if not os.path.exists(os.path.join(settings.MEDIA_ROOT, filename)):
            raise Exception("Файл не был создан после сохранения")
            
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Ошибка при импорте шаблона: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': f'Ошибка при сохранении: {str(e)}'
        }, status=500)

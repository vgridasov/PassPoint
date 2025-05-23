from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Employee, Department, Position
from .forms import EmployeeForm, DepartmentForm, PositionForm
from django.core.paginator import Paginator
from django.db.models.functions import Lower
from django.db.models import Q

def is_admin(user):
    return user.is_superuser or user.groups.filter(name='Администратор').exists()

@login_required
def employee_list(request):
    employees = Employee.objects.all().order_by('last_name', 'first_name')
    search_query = request.GET.get('search', '')
    if search_query:
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

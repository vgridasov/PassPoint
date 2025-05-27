from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('employee/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employee/new/', views.employee_create, name='employee_create'),
    path('employee/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('departments/', views.department_list, name='department_list'),
    path('departments/new/', views.department_create, name='department_create'),
    path('positions/', views.position_list, name='position_list'),
    path('positions/new/', views.position_create, name='position_create'),
    path('department/<int:department_id>/employees/', views.employees_by_department, name='employees_by_department'),
    path('position/<int:position_id>/employees/', views.employees_by_position, name='employees_by_position'),
    path('employee/<int:pk>/create-pass/', views.create_pass, name='create_pass'),
    path('employee/import-pass-template/', views.import_pass_template, name='import_pass_template'),
] 
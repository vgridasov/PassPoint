from django import forms
from .models import Employee, Department, Position

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['last_name', 'first_name', 'middle_name', 'department', 'position', 'photo', 'is_fired', 'has_pass', 'lost_pass']
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.Select(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_fired': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_pass': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'lost_pass': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        } 
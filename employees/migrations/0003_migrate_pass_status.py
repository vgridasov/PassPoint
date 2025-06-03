from django.db import migrations

def migrate_pass_status_forward(apps, schema_editor):
    """
    Переносим данные из has_pass и lost_pass в pass_status
    """
    Employee = apps.get_model('employees', 'Employee')
    
    for employee in Employee.objects.all():
        if employee.has_pass:
            if employee.lost_pass:
                employee.pass_status = 'withdrawn'
            else:
                employee.pass_status = 'issued'
        else:
            employee.pass_status = 'none'
        employee.save(update_fields=['pass_status'])

def migrate_pass_status_backward(apps, schema_editor):
    """
    Восстанавливаем has_pass из pass_status при откате миграции
    """
    Employee = apps.get_model('employees', 'Employee')
    
    for employee in Employee.objects.all():
        if employee.pass_status in ['issued', 'ready']:
            employee.has_pass = True
        else:
            employee.has_pass = False
        employee.save(update_fields=['has_pass'])

class Migration(migrations.Migration):
    dependencies = [
        ('employees', '0002_add_pass_status'),
    ]

    operations = [
        migrations.RunPython(
            migrate_pass_status_forward,
            migrate_pass_status_backward
        ),
        migrations.RemoveField(
            model_name='employee',
            name='has_pass',
        ),
    ] 
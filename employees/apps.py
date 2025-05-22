from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver


class EmployeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'employees'

@receiver(post_migrate)
def create_groups(sender, **kwargs):
    from django.contrib.auth.models import Group
    for group_name in ['Администратор', 'Контролёр']:
        Group.objects.get_or_create(name=group_name)

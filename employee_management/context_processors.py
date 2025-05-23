from django.conf import settings

def organization_settings(request):
    """
    Контекстный процессор для передачи настроек организации в шаблоны
    """
    return {
        'settings': {
            'ORGANIZATION_NAME': settings.ORGANIZATION_NAME,
            'ORGANIZATION_ADDRESS': settings.ORGANIZATION_ADDRESS,
            'ORGANIZATION_PHONE': settings.ORGANIZATION_PHONE,
            'ORGANIZATION_EMAIL': settings.ORGANIZATION_EMAIL,
        }
    } 
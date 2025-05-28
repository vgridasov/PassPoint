from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Настройка заголовков админки
admin.site.site_header = "Панель администратора"
admin.site.site_title = "Панель администратора"
admin.site.index_title = "Управление системой"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('employees.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
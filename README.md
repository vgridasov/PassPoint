# Система управления персоналом

Система для управления данными сотрудников, включая их профили, подразделения и должности.

## Требования к системе

- Python 3.13+
- PostgreSQL 15+
- Nginx
- Ubuntu 22.04 LTS или новее
- 2GB RAM минимум
- 20GB свободного места на диске

## Установка для разработки

1. Клонировать репозиторий:
```bash
git clone https://github.com/your-username/inventory.git
cd inventory
```

2. Создать виртуальное окружение:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. Установить зависимости:
```bash
pip install -r requirements.txt
```

4. Создать файл .env:
```bash
cp .env.example .env
# Отредактировать .env, заполнив необходимые значения
```

5. Применить миграции:
```bash
python manage.py migrate
```

6. Создать суперпользователя:
```bash
python manage.py createsuperuser
```

7. Собрать статические файлы:
```bash
python manage.py collectstatic
```

8. Запустить сервер:
```bash
python manage.py runserver
```

## Деплой на продакшен

### 1. Подготовка сервера

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить необходимые пакеты
sudo apt install python3.13 python3.13-venv postgresql postgresql-contrib nginx supervisor -y
```

### 2. Настройка PostgreSQL

```bash
# Войти в PostgreSQL
sudo -u postgres psql

# Создать базу данных и пользователя
CREATE DATABASE inventory;
CREATE USER inventory_user WITH PASSWORD 'your_secure_password';
ALTER ROLE inventory_user SET client_encoding TO 'utf8';
ALTER ROLE inventory_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE inventory_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE inventory TO inventory_user;
\q
```

### 3. Настройка Nginx

```bash
# Создать конфигурацию
sudo nano /etc/nginx/sites-available/inventory

# Добавить конфигурацию
server {
    listen 80;
    server_name your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/inventory;
    }

    location /media/ {
        root /var/www/inventory;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}

# Активировать конфигурацию
sudo ln -s /etc/nginx/sites-available/inventory /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Настройка SSL с Let's Encrypt

```bash
# Установить Certbot
sudo apt install certbot python3-certbot-nginx

# Получить сертификат
sudo certbot --nginx -d your-domain.com

# Настроить автообновление
sudo certbot renew --dry-run
```

### 5. Настройка Gunicorn

```bash
# Создать конфигурацию
sudo nano /etc/supervisor/conf.d/inventory.conf

# Добавить конфигурацию
[program:inventory]
directory=/var/www/inventory
command=/var/www/inventory/.venv/bin/gunicorn employee_management.wsgi:application --workers 3 --bind unix:/run/gunicorn.sock
autostart=true
autorestart=true
stderr_logfile=/var/log/inventory/gunicorn.err.log
stdout_logfile=/var/log/inventory/gunicorn.out.log
user=www-data
group=www-data
environment=
    DJANGO_SETTINGS_MODULE="employee_management.settings",
    PATH="/var/www/inventory/.venv/bin"

# Перезапустить Supervisor
sudo supervisorctl reread
sudo supervisorctl update
```

### 6. Деплой приложения

```bash
# Создать директорию
sudo mkdir -p /var/www/inventory

# Клонировать репозиторий
sudo git clone https://github.com/vgridasov/inventory.git /var/www/inventory

# Установить права
sudo chown -R www-data:www-data /var/www/inventory
sudo chmod -R 755 /var/www/inventory

# Создать и активировать виртуальное окружение
cd /var/www/inventory
python3.13 -m venv .venv
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Создать .env файл
sudo nano .env
# Заполнить необходимые переменные окружения

# Применить миграции
python manage.py migrate

# Собрать статические файлы
python manage.py collectstatic

# Перезапустить Gunicorn
sudo supervisorctl restart inventory
```

## Структура проекта

```
inventory/
├── employees/          # Основное приложение
├── templates/          # Шаблоны
├── static/            # Статические файлы
├── media/             # Загружаемые файлы
├── logs/              # Логи
└── manage.py          # Скрипт управления
```

## Тестирование

```bash
# Запуск тестов
pytest

# Запуск тестов с отчетом о покрытии
pytest --cov=employees
```

## Лицензия

MIT 
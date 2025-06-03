from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='pass_status',
            field=models.CharField(
                choices=[
                    ('none', 'Нет'),
                    ('ready', 'Готов'),
                    ('issued', 'Выдан'),
                    ('withdrawn', 'Изъят/Аннулирован'),
                ],
                default='none',
                max_length=10,
                verbose_name='Статус пропуска'
            ),
        ),
    ] 
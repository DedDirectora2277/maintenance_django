# Generated by Django 5.1.4 on 2024-12-07 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='maintenancestandard',
            name='maintenance_type',
            field=models.CharField(choices=[('ТО', 'Технический осмотр'), ('ТР', 'Технический ремонт'), ('КР', 'Капитальный ремонт')], default='ТО', max_length=2),
        ),
    ]
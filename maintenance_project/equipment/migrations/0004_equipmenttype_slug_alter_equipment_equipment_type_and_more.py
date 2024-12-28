# Generated by Django 5.0.4 on 2024-12-25 15:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0003_alter_equipment_options_equipment_image'),
    ]

    operations = [ 
        migrations.AddField(
            model_name='equipmenttype',
            name='slug',
            field=models.SlugField(blank=True, max_length=255, verbose_name='Слаг'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='equipment_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='equipments', to='equipment.equipmenttype', verbose_name='Тип оборудования'),
        ),
        migrations.AlterField(
            model_name='equipmentmaintenancetype',
            name='equipment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenance_types_eq', to='equipment.equipment', verbose_name='Оборудование'),
        ),
        migrations.AlterField(
            model_name='equipmentmaintenancetype',
            name='maintenance_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenance_types_mt', to='equipment.maintenancetype', verbose_name='Тип обслуживания'),
        ),
        migrations.AlterField(
            model_name='maintenanceschedule',
            name='equipment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenance_schedules', to='equipment.equipment', verbose_name='Оборудование'),
        ),
    ]

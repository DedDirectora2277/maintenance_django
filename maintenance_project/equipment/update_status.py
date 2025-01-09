# -*- coding: utf-8 -*-

from .models import MaintenanceSchedule

def run():
    """Обновляет статусы обслуживания на русские значения."""

    status_map = {
        'scheduled': 'Запланировано',
        'completed': 'Выполнено',
        'overdue': 'Просрочено',
    }

    for old_status, new_status in status_map.items():
        MaintenanceSchedule.objects.filter(status=old_status).update(status=new_status)

    print("Статусы обновлены!")
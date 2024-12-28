import datetime
from django.utils import timezone

from .models import MaintenanceSchedule


def generate_schedule(equipment):
    """
    Генерирует график технического обслуживания для
    оборудования на основе нормативов.

    :param equipment: Объект модели Equipment
    :return: Список объектов MaintenanceSchedule
    """
    today = datetime.date.today()
    standards = equipment.maintenancestandard_set.all()
    schedule = []

    for standard in standards:
        next_date = today
        while next_date < today + datetime.timedelta(days=365):
            next_date += datetime.timedelta(days=standard.interval_days)
            schedule.append(MaintenanceSchedule(
                equipment=equipment,
                maintenance_type=standard.maintenance_type,
                date=next_date
            ))

    # Возвращаем список созданных объектов
    return schedule 


def filter_equipment(equipments):
    """
    Фильтрует переданный queryset оборудования по следующим критериям:
    1. is_displayed у EquipmentType = True
    2. is_displayed у Equipment = True
    3. installation_date <= текущей даты
    """
    today = timezone.now().date()
    equipments = equipments.filter(
        equipment_type__is_displayed=True,
        is_displayed=True,
        installation_date__lte=today
    )
    return equipments

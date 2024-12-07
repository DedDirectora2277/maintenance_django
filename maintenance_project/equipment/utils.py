import datetime
from .models import MaintenanceSchedule


def generate_schedule(equipment):
    """
    Генерирует график технического обслуживания для оборудования на основе нормативов.

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
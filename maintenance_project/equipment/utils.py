from django.utils import timezone
from calendar import monthrange


def prepare_calendar_data(year, month, schedule_items):
    """
    Подготавливает данные для отображения календаря.

    Args:
        year: Год.
        month: Номер месяца.
        schedule_items: Queryset или список объектов с атрибутом planned_date.

    Returns:
        Список недель, каждая из которых является списком словарей с данными дня.
    """
    days_in_month = monthrange(year, month)[1]
    first_day_weekday = timezone.datetime(year, month, 1).weekday()

    calendar_data = []
    week = []

    # Заполняем пустые дни в начале месяца
    for _ in range(first_day_weekday):
        week.append({"day": None, "items": []})

    schedule_by_day = {}
    for item in schedule_items:
        day = item.planned_date.day
        if day not in schedule_by_day:
            schedule_by_day[day] = []
        schedule_by_day[day].append(item)

    # Заполняем календарь
    for day in range(1, days_in_month + 1):
        current_date = timezone.datetime(year, month, day)
        is_today = current_date.date() == timezone.now().date()
        week.append(
            {
                "day": day,
                "items": schedule_by_day.get(day, []),
                "is_today": is_today,
                "is_weekend": current_date.weekday() in (5, 6),
            }
        )
        if len(week) == 7:
            calendar_data.append(week)
            week = []

    # Заполняем пустые дни в конце месяца
    while len(week) < 7:
        week.append({"day": None, "items": []})
    if week:
        calendar_data.append(week)

    return calendar_data


def filter_equipment(equipments):
    """
    Фильтрует переданный queryset оборудования по следующим критериям:

    1. is_displayed у EquipmentType = True
    2. is_displayed у Equipment = True
    3. installation_date <= текущей даты

    Args:
        equipments: QuerySet объектов Equipment.

    Returns:
        QuerySet объектов Equipment, отфильтрованный по заданным критериям.
    """
    today = timezone.now().date()
    equipments = equipments.filter(
        equipment_type__is_displayed=True,
        is_displayed=True,
        installation_date__lte=today,
    )
    return equipments
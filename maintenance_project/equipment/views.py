from django.shortcuts import get_object_or_404, render

from .models import Equipment


def index(request):
    equipment_list = Equipment.objects.all()
    return render(request, 'equipment/index.html', {'equipment_list': equipment_list})


def equipment_type(request, type):
    """
    Отображает список оборудования указанного типа.
    """
    equipment_list = Equipment.objects.filter(type=type)
    return render(request, 
                  'equipment/equipment_type.html', 
                  {'equipment_list': equipment_list, 'equipment_type': type}
            )


def equipment_schedule(request, equipment_id):
    """
    Отображает график обслуживания для конкретного оборудования.
    """
    equipment = get_object_or_404(Equipment, id=equipment_id)
    schedule = equipment.maintenance_schedules.all().order_by('date')
    return render(request, 
                  'equipment/schedule.html', 
                  {'equipment': equipment,'schedule': schedule,}
           )
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView

from .utils import filter_equipment

from .models import Equipment, EquipmentType


PAGES = 3


class EquipmentListView(ListView):
    model = Equipment
    template_name = 'equipment/index.html'
    context_object_name = 'equipment_list'
    paginate_by = PAGES

    def get_queryset(self):
        queryset = Equipment.objects.all().select_related('equipment_type')
        queryset = filter_equipment(queryset)
        return queryset


class EquipmentTypeListView(ListView):
    model = Equipment
    template_name = 'equipment/equipment_type.html'
    context_object_name = 'equipment_list'
    paginate_by = PAGES

    def get_queryset(self):
        slug = self.kwargs['type_slug']
        equipment_type = get_object_or_404(
            EquipmentType, slug=slug, is_displayed=True
        )
        queryset = equipment_type.equipments.all()\
            .select_related('equipment_type')
        queryset = filter_equipment(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipment_type'] = get_object_or_404(
            EquipmentType,
            slug=self.kwargs['type_slug'],
            is_displayed=True
        )
        return context


class EquipmentDetailView(DetailView):
    model = Equipment
    template_name = 'equipment/detail.html'
    context_object_name = 'equipment'
    pk_url_kwarg = 'equipment_id'


def equipment_schedule(request, equipment_id):
    try:
        equipment = Equipment.objects.get(id=equipment_id)
    except Equipment.DoesNotExist:
        raise Http404(f"Оборудование с id {equipment_id} не найдено")

    schedule = equipment.maintenance_schedules.all().order_by('date')
    return render(request,
                  'equipment/schedule.html',
                  {'equipment': equipment, 'schedule': schedule, })

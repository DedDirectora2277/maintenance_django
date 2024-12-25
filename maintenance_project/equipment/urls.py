from django.urls import path
from . import views

app_name = 'equipment'


urlpatterns = [
    path('', views.EquipmentListView.as_view(), name='index'),
    path('schedule/<int:equipment_id>',
          views.equipment_schedule,
          name='equipment_schedule'),
    path('type/<slug:type_slug>/',
          views.EquipmentTypeListView.as_view(),
          name='equipment_type'),
    path('equipment/<int:equipment_id>',
         views.EquipmentDetailView.as_view(),
         name='equipment_detail')
]

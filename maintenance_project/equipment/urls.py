from django.urls import path
from . import views

app_name = 'equipment'


urlpatterns = [
    path('', views.index, name='index'),
    path('schedule/<int:equipment_id>',
          views.equipment_schedule,
          name='equipment_schedule'
    ),
    path('type/<str:type>/',
          views.equipment_type, 
          name='equipment_type'
    ),
]
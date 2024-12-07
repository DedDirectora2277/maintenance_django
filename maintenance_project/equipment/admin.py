from django.contrib import admin

from .models import Equipment, MaintenanceStandard, MaintenanceSchedule


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'model')


@admin.register(MaintenanceStandard)
class MaintenanceStandardAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'interval_to', 'interval_tr', 'interval_kr')
    
    list_filter = ('interval_to', 'interval_tr', 'interval_kr')


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'maintenance_type', 'date')  
    list_filter = ('maintenance_type', 'date')               
    search_fields = ('equipment__name', 'maintenance_type')  


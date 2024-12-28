from django.contrib import admin
from .models import (Equipment, EquipmentType, EquipmentMaintenance, MaintenanceSchedule)


class EquipmentMaintenanceInline(admin.StackedInline):
    model = EquipmentMaintenance
    can_delete = False
    verbose_name_plural = 'Периодичности обслуживания'


@admin.register(Equipment) 
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'equipment_type', 'model', 'manufacturer', 'get_to_periodicity', 'get_tr_periodicity', 'get_kr_periodicity')
    inlines = [EquipmentMaintenanceInline]

    def get_to_periodicity(self, obj):
        return obj.maintenance.to_periodicity if hasattr(obj, 'maintenance') else None
    get_to_periodicity.short_description = 'ТО (дни)'

    def get_tr_periodicity(self, obj):
        return obj.maintenance.tr_periodicity if hasattr(obj, 'maintenance') and obj.maintenance.tr_periodicity else None
    get_tr_periodicity.short_description = 'ТР (дни)'

    def get_kr_periodicity(self, obj):
        return obj.maintenance.kr_periodicity if hasattr(obj, 'maintenance') and obj.maintenance.kr_periodicity else None
    get_kr_periodicity.short_description = 'КР (дни)'


@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_displayed')


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'maintenance_type', 'planned_date', 'actual_date', 'status', 'notes')
    list_filter = ('equipment', 'maintenance_type', 'status')
    list_editable = ('status', 'notes', 'actual_date')
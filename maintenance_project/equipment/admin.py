from django.contrib import admin
from .models import (
    Equipment, MaintenanceType,
    EquipmentMaintenanceType, MaintenanceSchedule,
    EquipmentType,
)


class EquipmentMaintenanceTypeInline(admin.TabularInline):
    model = EquipmentMaintenanceType
    extra = 0


@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_displayed', 'slug')
    list_filter = ('is_displayed',)
    list_editable = ('is_displayed', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    inlines = [EquipmentMaintenanceTypeInline]
    list_display = (
        'name', 'model', 'manufacturer', 'serial_number',
        'inventory_number', 'installation_date', 'get_maintenance_types',
        'is_displayed',
    )
    search_fields = (
        'name', 'model', 'manufacturer', 'serial_number', 'inventory_number'
    )
    list_editable = ('is_displayed',)

    def get_maintenance_types(self, obj):
        return ", ".join([mt.name for mt in obj.maintenance_types.all()])
    get_maintenance_types.short_description = 'Типы обслуживания'


@admin.register(MaintenanceType)
class MaintenanceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'periodicity')
    search_fields = ('name',)


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'equipment', 'maintenance_type', 'planned_date',
        'actual_date', 'status'
    )
    list_filter = ('status', 'maintenance_type', 'planned_date')
    search_fields = ('equipment__name', 'notes')

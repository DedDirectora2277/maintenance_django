from datetime import timedelta
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils import timezone


class Displayable(models.Model):
    is_displayed = models.BooleanField(default=True,
                                       verbose_name="Отображать на сайте")
    description = models.TextField(blank=True,
                                   verbose_name="Описание")

    class Meta:
        abstract = True


class EquipmentType(Displayable):
    name = models.CharField(max_length=255, unique=True,
                            verbose_name="Название типа оборудования")
    slug = models.SlugField(max_length=255, unique=True,
                            verbose_name="Слаг",
                            help_text=('Идентификатор страницы для URL; '
                                       'разрешены символы латиницы, цифры, '
                                       'дефис и подчёркивание.'))

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Тип оборудования"
        verbose_name_plural = "Типы оборудования"


class Equipment(Displayable):
    equipment_type = models.ForeignKey(EquipmentType,
                                       on_delete=models.SET_NULL,
                                       null=True,
                                       blank=True,
                                       verbose_name="Тип оборудования",
                                       related_name="equipments")
    name = models.CharField(max_length=255, verbose_name="Название")
    model = models.CharField(max_length=255, verbose_name="Модель")
    manufacturer = models.CharField(max_length=255,
                                    verbose_name="Производитель")
    serial_number = models.CharField(max_length=255,
                                     verbose_name="Серийный номер")
    inventory_number = models.CharField(max_length=255,
                                        verbose_name="Инвентарный номер")
    installation_date = models.DateField(
        verbose_name="Дата ввода в эксплуатацию"
    )
    image = models.ImageField(upload_to='equipment_images/',
                              verbose_name="Изображение",
                              null=True,
                              blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"
        ordering = ["-installation_date"]

    def get_maintenance_types(self):
        maintenance_types = []
        if self.to_periodicity:
            maintenance_types.append(f"ТО ({self.to_periodicity} дн.)")
        if self.tr_periodicity:
            maintenance_types.append(f"ТР ({self.tr_periodicity} дн.)")
        if self.kr_periodicity:
            maintenance_types.append(f"КР ({self.kr_periodicity} дн.)")

        return ", ".join(maintenance_types)
    get_maintenance_types.short_description = 'Типы обслуживания'


class EquipmentMaintenance(models.Model):
    equipment = models.OneToOneField(Equipment,
                                   on_delete=models.CASCADE,
                                   verbose_name="Оборудование",
                                   related_name="maintenance")
    to_periodicity = models.IntegerField(
        verbose_name="Периодичность ТО (дни)"
    )
    tr_periodicity = models.IntegerField(
        null=True, blank=True,
        verbose_name="Периодичность ТР (дни)"
    )
    kr_periodicity = models.IntegerField(
        null=True, blank=True,
        verbose_name="Периодичность КР (дни)"
    )

    def __str__(self):
        return f"Периодичности обслуживания для {self.equipment.name}"

    def clean(self):
        if self.tr_periodicity:
            if self.tr_periodicity % self.to_periodicity != 0:
                raise ValidationError(
                    "Периодичность 'ТР' должна быть кратна периодичности "
                    f"ТО ({self.to_periodicity} дн.)."
                )

        if self.kr_periodicity:
            if not self.tr_periodicity:
                raise ValidationError(
                    "Для задания периодичности 'КР' необходимо указать "
                    "периодичность 'ТР'."
                )
            if (self.kr_periodicity % self.to_periodicity != 0
                    or self.kr_periodicity % self.tr_periodicity != 0):
                raise ValidationError(
                    "Периодичность 'КР' должна быть кратна периодичности "
                    f"ТО ({self.to_periodicity} дн.) и ТР ({self.tr_periodicity} дн.)."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Периодичность обслуживания оборудования"
        verbose_name_plural = "Периодичности обслуживания оборудования"


class MaintenanceSchedule(models.Model):
    MAINTENANCE_TYPE_CHOICES = (
        ('to', 'ТО'),
        ('tr', 'ТР'),
        ('kr', 'КР'),
    )

    STATUS_CHOICES = (
        ('scheduled', 'Запланировано'),
        ('completed', 'Выполнено'),
        ('overdue', 'Просрочено'),
    )
    equipment = models.ForeignKey(Equipment,
                                  on_delete=models.CASCADE,
                                  verbose_name="Оборудование",
                                  related_name="maintenance_schedules")
    maintenance_type = models.CharField(max_length=2,
                                        choices=MAINTENANCE_TYPE_CHOICES,
                                        verbose_name="Тип обслуживания")
    planned_date = models.DateField(verbose_name="Запланированная дата")
    actual_date = models.DateField(null=True,
                                   blank=True,
                                   verbose_name="Фактическая дата")
    status = models.CharField(max_length=20,
                              choices=STATUS_CHOICES,
                              default='scheduled',
                              verbose_name="Статус")
    notes = models.TextField(blank=True, verbose_name="Заметки")

    def __str__(self):
        return (f"{self.equipment.name} - {self.get_maintenance_type_display()} -"
                f" {self.planned_date}")

    class Meta:
        verbose_name = "График обслуживания"
        verbose_name_plural = "Графики обслуживания"


def generate_schedule(equipment, start_date=None, end_date=None):
    """
    Функция для создания записей в графике обслуживания.
    """
    if not hasattr(equipment, 'maintenance'):
        return

    if start_date is None:
        start_date = timezone.now().date()

    if end_date is None:
        end_date = start_date + timedelta(days=365)
    
    # Удалим уже созданные записи, чтобы не было конфликтов
    MaintenanceSchedule.objects.filter(
        equipment=equipment,
        planned_date__gte=start_date,
        planned_date__lte=end_date
    ).delete()

    periodicity_map = {
        'to': equipment.maintenance.to_periodicity,
        'tr': equipment.maintenance.tr_periodicity,
        'kr': equipment.maintenance.kr_periodicity
    }

    for maintenance_type, periodicity in periodicity_map.items():
        if periodicity:
            current_date = start_date
            while current_date <= end_date:
                MaintenanceSchedule.objects.create(
                    equipment=equipment,
                    maintenance_type=maintenance_type,
                    planned_date=current_date,
                    status='scheduled'
                )
                current_date += timedelta(days=periodicity)
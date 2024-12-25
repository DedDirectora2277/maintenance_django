from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify


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
                            verbose_name="Слаг", blank=True,
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
    maintenance_types = models.ManyToManyField(
        'MaintenanceType',
        through='EquipmentMaintenanceType',
        verbose_name="Типы обслуживания"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"
        ordering = ["-installation_date"]


class MaintenanceType(models.Model):
    name = models.CharField(max_length=255, unique=True,
                            verbose_name="Название типа обслуживания")
    periodicity = models.IntegerField(
        verbose_name="Базовая периодичность (дни)"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип обслуживания"
        verbose_name_plural = "Типы обслуживания"


class EquipmentMaintenanceType(models.Model):
    equipment = models.ForeignKey(Equipment,
                                  on_delete=models.CASCADE,
                                  verbose_name="Оборудование",
                                  related_name="maintenance_types_eq")
    maintenance_type = models.ForeignKey(MaintenanceType,
                                         on_delete=models.CASCADE,
                                         verbose_name="Тип обслуживания",
                                         related_name="maintenance_types_mt")
    periodicity = models.IntegerField(
        verbose_name="Индивидуальная периодичность (дни)"
    )

    def __str__(self):
        return f"{self.equipment.name} - {self.maintenance_type.name}"

    def clean(self):
        # Проверка кратности периодичностей
        to_periodicity = EquipmentMaintenanceType.objects.filter(
            equipment=self.equipment,
            maintenance_type__name="ТО"
        ).values_list('periodicity', flat=True).first()

        tr_periodicity = EquipmentMaintenanceType.objects.filter(
            equipment=self.equipment,
            maintenance_type__name="ТР"
        ).values_list('periodicity', flat=True).first()

        if self.maintenance_type.name == "ТО":
            # Для ТО другие периодичности не проверяем (базовый тип)
            pass
        elif self.maintenance_type.name == "ТР":
            if not to_periodicity:
                raise ValidationError(
                    "Для данного оборудования не задана периодичность ТО."
                )
            if self.periodicity % to_periodicity != 0:
                raise ValidationError(
                    "Периодичность 'ТР' должна быть кратна периодичности "
                    f"ТО ({to_periodicity} дн.)."
                )
        elif self.maintenance_type.name == "КР":
            if not to_periodicity:
                raise ValidationError(
                    "Для данного оборудования не задана периодичность ТО."
                )
            if not tr_periodicity:
                raise ValidationError(
                    "Для данного оборудования не задана периодичность ТР."
                )
            if (self.periodicity % to_periodicity != 0
                    or self.periodicity % tr_periodicity != 0):
                raise ValidationError(
                    "Периодичность 'КР' должна быть кратна периодичности "
                    f"ТО ({to_periodicity} дн.) и ТР ({tr_periodicity} дн.)."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Периодичность обслуживания оборудования"
        verbose_name_plural = "Периодичности обслуживания оборудования"
        unique_together = ('equipment', 'maintenance_type')


class MaintenanceSchedule(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Запланировано'),
        ('completed', 'Выполнено'),
        ('overdue', 'Просрочено'),
    )
    equipment = models.ForeignKey(Equipment,
                                  on_delete=models.CASCADE,
                                  verbose_name="Оборудование",
                                  related_name="maintenance_schedules")
    maintenance_type = models.ForeignKey(MaintenanceType,
                                         on_delete=models.CASCADE,
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
        return (f"{self.equipment.name} - {self.maintenance_type.name} -"
                f" {self.planned_date}")

    class Meta:
        verbose_name = "График обслуживания"
        verbose_name_plural = "Графики обслуживания"

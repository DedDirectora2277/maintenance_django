from datetime import date, timedelta
from django.db import models
from django.forms import ValidationError


class Equipment(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class MaintenanceStandard(models.Model):
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name="maintenance_standard")
    interval_to = models.IntegerField(help_text="Интервал для ТО (в днях)")
    interval_tr = models.IntegerField(help_text="Интервал для ТР (в днях)")
    interval_kr = models.IntegerField(help_text="Интервал для КР (в днях)")

    def clean(self):
        """
        Проверяет, что интервалы для ТО, ТР и КР кратны друг другу.
        """
        intervals = [self.interval_to, self.interval_tr, self.interval_kr]
        for i in range(len(intervals)):
            for j in range(i + 1, len(intervals)):
                if intervals[i] % intervals[j] != 0 and intervals[j] % intervals[i] != 0:
                    raise ValidationError(
                        f"Интервалы {intervals[i]} и {intervals[j]} не кратны друг другу. "
                        f"Убедитесь, что все интервалы обслуживания кратны."
                    )

    def save(self, *args, **kwargs):
        # Вызываем проверку на кратность
        self.clean()
        super().save(*args, **kwargs)
        # После сохранения создаем расписание
        self.generate_schedule()

    def generate_schedule(self):
        """
        Генерация расписания для оборудования до 3-го капитального ремонта.
        """
        end_date = date.today() + timedelta(days=3 * self.interval_kr)
        current_date = date.today()

        schedule_entries = []

        while current_date <= end_date:
            if (current_date - date.today()).days % self.interval_to == 0 \
                        and (current_date - date.today()).days != 0:
                schedule_entries.append(MaintenanceSchedule(
                    equipment=self.equipment,
                    maintenance_type="ТО",
                    date=current_date
                ))

            if (current_date - date.today()).days % self.interval_tr == 0 \
                        and (current_date - date.today()).days != 0:
                schedule_entries.append(MaintenanceSchedule(
                    equipment=self.equipment,
                    maintenance_type="ТР",
                    date=current_date
                ))

            if (current_date - date.today()).days % self.interval_kr == 0 \
                        and (current_date - date.today()).days != 0:
                schedule_entries.append(MaintenanceSchedule(
                    equipment=self.equipment,
                    maintenance_type="КР",
                    date=current_date
                ))

            current_date += timedelta(days=1)

        MaintenanceSchedule.objects.bulk_create(schedule_entries)

    def __str__(self):
        return f"Нормативы для {self.equipment.name}"


class MaintenanceSchedule(models.Model):
    equipment = models.ForeignKey(
        Equipment, 
        on_delete=models.CASCADE, 
        related_name="maintenance_schedules"
    )
    maintenance_type = models.CharField(max_length=50)
    date = models.DateField()

    def __str__(self):
        return f"{self.date}: {self.equipment.name} ({self.maintenance_type})"
from calendar import monthrange

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.formats import date_format
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User

from .forms import (
    MaintenanceScheduleEditForm,
    ProfileEditForm,
    GenerateScheduleForm,
)
from .models import (
    Equipment,
    EquipmentType,
    MaintenanceSchedule,
    generate_schedule,
)
from .utils import filter_equipment, prepare_calendar_data


PAGES = 3


class CalendarMixin:
    def get_current_year_month(self):
        today = timezone.now()
        year = self.request.GET.get("year", today.year)
        month = self.request.GET.get("month", today.month)
        try:
            year = int(year)
            month = int(month)
        except ValueError:
            raise Http404("Неверный формат года или месяца.")

        if not 1 <= month <= 12:
            raise Http404("Неверный номер месяца.")
        return year, month

    def get_previous_month_and_year(self, month, year):
        prev_month = month - 1
        prev_year = year
        if prev_month < 1:
            prev_month = 12
            prev_year -= 1
        return prev_month, prev_year

    def get_next_month_and_year(self, month, year):
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1
        return next_month, next_year

    def get_calendar_data(self, year, month, queryset):
        start_date = timezone.datetime(year, month, 1).date()
        days_in_month = monthrange(year, month)[1]
        end_date = timezone.datetime(year, month, days_in_month).date()

        schedule = queryset.filter(
            planned_date__gte=start_date, planned_date__lte=end_date
        ).order_by("planned_date")

        calendar_data = prepare_calendar_data(year, month, schedule)
        return calendar_data, schedule

    def get_month_navigation_urls(self, month, year):
        prev_month, prev_year = self.get_previous_month_and_year(month, year)
        next_month, next_year = self.get_next_month_and_year(month, year)

        prev_month_url = f"?year={prev_year}&month={prev_month}"
        next_month_url = f"?year={next_year}&month={next_month}"

        return prev_month_url, next_month_url


class EquipmentListView(ListView):
    model = Equipment
    template_name = "equipment/index.html"
    context_object_name = "equipment_list"
    paginate_by = PAGES

    def get_queryset(self):
        queryset = Equipment.objects.all().select_related("equipment_type")
        queryset = filter_equipment(queryset)
        return queryset


class EquipmentTypeListView(ListView):
    model = Equipment
    template_name = "equipment/equipment_type.html"
    context_object_name = "equipment_list"
    paginate_by = PAGES

    def get_queryset(self):
        slug = self.kwargs["type_slug"]
        equipment_type = get_object_or_404(
            EquipmentType, slug=slug, is_displayed=True
        )
        queryset = (
            equipment_type.equipments.all().select_related("equipment_type")
        )
        queryset = filter_equipment(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["equipment_type"] = get_object_or_404(
            EquipmentType, slug=self.kwargs["type_slug"], is_displayed=True
        )
        return context


class EquipmentDetailView(CalendarMixin, DetailView):
    model = Equipment
    template_name = "equipment/detail.html"
    context_object_name = "equipment"
    pk_url_kwarg = "equipment_id"

    def get_queryset(self):
        return Equipment.objects.all().prefetch_related("maintenance_schedules")

    def get_context_data(self, **kwargs):
        MaintenanceSchedule.objects.update_overdue_status()
        context = super().get_context_data(**kwargs)
        equipment = self.get_object()

        year, month = self.get_current_year_month()

        calendar_data, schedule = self.get_calendar_data(
            year,
            month,
            equipment.maintenance_schedules.all(),
        )

        prev_month_url, next_month_url = self.get_month_navigation_urls(
            month, year
        )

        context["schedule"] = schedule
        context["calendar_data"] = calendar_data
        context["current_year"] = year
        context["current_month"] = month
        context["month_name"] = date_format(
            timezone.datetime(year, month, 1).date(), "F"
        )
        context["prev_month_url"] = prev_month_url
        context["next_month_url"] = next_month_url
        context["form"] = GenerateScheduleForm()

        try:
            equipment_maintenance = equipment.maintenance
        except Equipment.DoesNotExist:
            equipment_maintenance = None

        context["equipment_maintenance"] = equipment_maintenance

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        equipment = self.object
        form = GenerateScheduleForm(request.POST)
        if form.is_valid():
            end_date = form.cleaned_data["end_date"]
            generate_schedule(
                equipment,
                start_date=equipment.installation_date,
                end_date=end_date,
            )
            messages.success(
                request,
                f"Расписание успешно создано до {end_date.strftime('%d.%m.%Y')}.",
            )
            return redirect(
                reverse(
                    "equipment:equipment_detail",
                    kwargs={"equipment_id": equipment.pk},
                )
            )
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
            context = self.get_context_data(**kwargs)
            context["form"] = form
            return self.render_to_response(context)


class ScheduleView(CalendarMixin, ListView):
    model = MaintenanceSchedule
    template_name = "equipment/schedule.html"
    context_object_name = "schedule"
    paginate_by = 10

    def get_queryset(self):
        MaintenanceSchedule.objects.update_overdue_status()
        year, month = self.get_current_year_month()
        start_date = timezone.datetime(year, month, 1).date()
        days_in_month = monthrange(year, month)[1]
        end_date = timezone.datetime(year, month, days_in_month).date()
        queryset = (
            MaintenanceSchedule.objects.select_related("equipment")
            .filter(planned_date__gte=start_date, planned_date__lte=end_date)
            .order_by("planned_date", "equipment")
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year, month = self.get_current_year_month()
        calendar_data, _ = self.get_calendar_data(
            year,
            month,
            self.get_queryset(),
        )

        prev_month_url, next_month_url = self.get_month_navigation_urls(
            month, year
        )

        context["calendar_data"] = calendar_data
        context["current_year"] = year
        context["current_month"] = month
        context["month_name"] = date_format(
            timezone.datetime(year, month, 1).date(), "F"
        )
        context["prev_month_url"] = (
            prev_month_url + f"&edit_id={self.request.GET.get('edit_id', '')}"
        )
        context["next_month_url"] = (
            next_month_url + f"&edit_id={self.request.GET.get('edit_id', '')}"
        )

        return context


class MaintenanceScheduleUpdateView(LoginRequiredMixin, UpdateView):
    model = MaintenanceSchedule
    form_class = MaintenanceScheduleEditForm
    template_name = "equipment/schedule_edit.html"
    pk_url_kwarg = "maintenance_id"

    def get_success_url(self):
        return reverse_lazy(
            "equipment:equipment_detail",
            kwargs={"equipment_id": self.object.equipment.pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["equipment"] = self.object.equipment
        return context


class RegisterView(CreateView):
    template_name = "registration/registration_form.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("equipment:index")


class ProfileView(DetailView):
    model = User
    template_name = "equipment/profile.html"
    context_object_name = "profile"

    def get_object(self, queryset=None):
        return get_object_or_404(User, username=self.kwargs["username"])


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = "equipment/edit_profile.html"
    form_class = ProfileEditForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            "equipment:profile", kwargs={"username": self.request.user.username}
        )

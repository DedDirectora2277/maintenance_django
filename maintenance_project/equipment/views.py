from calendar import monthrange
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import FormView
from .forms import ProfileEditForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from .forms import GenerateScheduleForm

from .utils import filter_equipment

from .models import Equipment, EquipmentType, MaintenanceSchedule, generate_schedule


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipment = self.get_object()

        # Получаем текущий месяц и год
        today = timezone.now()
        year = self.request.GET.get('year', today.year)
        month = self.request.GET.get('month', today.month)
        try:
            year = int(year)
            month = int(month)
        except ValueError:
            raise Http404("Неверный формат года или месяца.")

        # Проверяем корректность месяца
        if not 1 <= month <= 12:
            raise Http404("Неверный номер месяца.")

        # Получаем расписание на выбранный месяц
        start_date = timezone.datetime(year, month, 1).date()
        days_in_month = monthrange(year, month)[1]
        end_date = timezone.datetime(year, month, days_in_month).date()

        schedule = MaintenanceSchedule.objects.filter(
            equipment=equipment,
            planned_date__gte=start_date,
            planned_date__lte=end_date
        ).order_by('planned_date')

        # Подготавливаем данные для календаря
        calendar_data = self.prepare_calendar_data(year, month, schedule)

        context['schedule'] = schedule
        context['calendar_data'] = calendar_data
        context['current_year'] = year
        context['current_month'] = month
        context['month_name'] = start_date.strftime('%B')

        prev_month = month - 1
        prev_year = year
        if prev_month < 1:
            prev_month = 12
            prev_year -= 1
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1
        context['prev_month_url'] = f"?year={prev_year}&month={prev_month}"
        context['next_month_url'] = f"?year={next_year}&month={next_month}"

        context['form'] = GenerateScheduleForm()
        try:
            equipment_maintenance = equipment.maintenance
        except Equipment.maintenance.RelatedObjectDoesNotExist:
            equipment_maintenance = None

        context['equipment_maintenance'] = equipment_maintenance

        return context

    def prepare_calendar_data(self, year, month, schedule):
        """
        Подготавливает данные для отображения календаря.
        """
        days_in_month = monthrange(year, month)[1]
        first_day_weekday = timezone.datetime(year, month, 1).weekday()

        calendar_data = []
        week = []

        for _ in range(first_day_weekday):
            week.append({'day': None, 'items': []})

        schedule_by_day = {}
        for item in schedule:
            day = item.planned_date.day
            if day not in schedule_by_day:
                schedule_by_day[day] = []
            schedule_by_day[day].append(item)

        # Заполняем календарь
        for day in range(1, days_in_month + 1):
            current_date = timezone.datetime(year, month, day)
            is_today = current_date.date() == timezone.now().date()
            week.append({
                'day': day,
                'items': schedule_by_day.get(day, []),
                'is_today': is_today,
                'is_weekend': current_date.weekday() in (5, 6),
            })
            if len(week) == 7:
                calendar_data.append(week)
                week = []

        while len(week) < 7:
            week.append({'day': None, 'items': []})
        if week:
            calendar_data.append(week)

        return calendar_data
    
    @method_decorator(login_required(login_url='/auth/login/'))
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        equipment = self.object
        form = GenerateScheduleForm(request.POST)
        if form.is_valid():
            end_date = form.cleaned_data['end_date']
            generate_schedule(equipment, end_date=end_date)
            messages.success(request, f'Расписание успешно создано до {end_date.strftime("%d.%m.%Y")}.')
            return redirect(reverse('equipment:equipment_detail', kwargs={'equipment_id': equipment.pk}))
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
            context = self.get_context_data(**kwargs)
            context['form'] = form
            return self.render_to_response(context)


class RegisterView(CreateView):
    template_name = 'registration/registration_form.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('equipment:index')


class ProfileView(DetailView):
    model = User
    template_name = 'equipment/profile.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        return get_object_or_404(User, username=self.kwargs['username'])


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'equipment/edit_profile.html'
    form_class = ProfileEditForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('profile', kwargs={'username': self.request.user.username})

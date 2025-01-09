from django.urls import path

from . import views


app_name = "equipment"


urlpatterns = [
    path("", views.EquipmentListView.as_view(), name="index"),
    path(
        "profile/edit/", views.EditProfileView.as_view(), name="edit_profile"
    ),
    path(
        "profile/<str:username>/", views.ProfileView.as_view(), name="profile"
    ),
    path(
        "type/<slug:type_slug>/",
        views.EquipmentTypeListView.as_view(),
        name="equipment_type",
    ),
    path(
        "equipment/<int:equipment_id>",
        views.EquipmentDetailView.as_view(),
        name="equipment_detail",
    ),
    path("schedule/", views.ScheduleView.as_view(), name="schedule"),
    path(
        "maintenance/<int:maintenance_id>/edit/",
        views.MaintenanceScheduleUpdateView.as_view(),
        name="maintenance_edit",
    ),
]

from django.urls import path
from . import views

app_name = "employees"

urlpatterns = [
    path("", views.EmployeeListView.as_view(), name="list"),
    path("add/", views.EmployeeCreateView.as_view(), name="add"),
    path("<int:pk>/", views.EmployeeDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.EmployeeUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.EmployeeDeleteView.as_view(), name="delete"),
    # Ish grafiklari
    path("schedules/", views.ScheduleListView.as_view(), name="schedule_list"),
    path("schedules/add/", views.ScheduleCreateView.as_view(), name="schedule_add"),
    path("schedules/<int:pk>/edit/", views.ScheduleUpdateView.as_view(), name="schedule_edit"),
    path("schedules/<int:pk>/delete/", views.ScheduleDeleteView.as_view(), name="schedule_delete"),
]

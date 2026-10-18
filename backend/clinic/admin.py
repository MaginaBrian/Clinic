from django.contrib import admin

from .models import Appointment, Doctor, Patient, WorkingHours


class WorkingHoursInline(admin.TabularInline):
    model = WorkingHours
    extra = 1


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("name", "specialty", "is_active")
    inlines = [WorkingHoursInline]


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email")
    search_fields = ("name", "phone", "email")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("start_time", "doctor", "patient", "status")
    list_filter = ("status", "doctor")
    date_hierarchy = "start_time"

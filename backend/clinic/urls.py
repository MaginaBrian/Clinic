from django.urls import path

from . import views

urlpatterns = [
    path("doctors", views.DoctorListView.as_view()),
    path("doctors/<int:doctor_id>/availability", views.DoctorAvailabilityView.as_view()),
    path("appointments", views.AppointmentCreateView.as_view()),
    path("appointments/<int:appointment_id>", views.AppointmentDetailView.as_view()),
    path("appointments/<int:appointment_id>/cancel", views.AppointmentCancelView.as_view()),
    path("appointments/<int:appointment_id>/reschedule", views.AppointmentRescheduleView.as_view()),
    path("patients", views.PatientCreateView.as_view()),
    path("patients/<int:patient_id>", views.PatientDetailView.as_view()),
    path("patients/<int:patient_id>/appointments", views.PatientAppointmentsView.as_view()),
]

from datetime import date

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import clock
from .models import Appointment, Doctor, Patient
from .serializers import (
    AppointmentSerializer,
    BookAppointmentSerializer,
    CancelSerializer,
    DoctorSerializer,
    PatientSerializer,
    RescheduleSerializer,
)
from .services import booking, slots


def _appointment_response(appt: Appointment, http_status=status.HTTP_200_OK) -> Response:
    appt = Appointment.objects.select_related("doctor", "patient").get(pk=appt.pk)
    return Response(AppointmentSerializer(appt).data, status=http_status)


class DoctorListView(APIView):
    def get(self, request):
        doctors = Doctor.objects.filter(is_active=True)
        return Response(DoctorSerializer(doctors, many=True).data)


class DoctorAvailabilityView(APIView):
    def get(self, request, doctor_id: int):
        try:
            doctor = Doctor.objects.prefetch_related("working_hours").get(pk=doctor_id, is_active=True)
        except Doctor.DoesNotExist:
            raise NotFound("Doctor not found.", "doctor_not_found")

        raw = request.query_params.get("date")
        if not raw:
            raise ValidationError({"date": ["This query parameter is required (YYYY-MM-DD)."]})
        try:
            day = date.fromisoformat(raw)
        except ValueError:
            raise ValidationError({"date": ["Use the format YYYY-MM-DD."]})

        free = slots.available_slots(doctor, day, clock.now())
        tz = slots.clinic_tz()
        step = slots.slot_length()
        return Response(
            {
                "doctor_id": doctor.pk,
                "date": day.isoformat(),
                "timezone": str(tz),
                "slot_minutes": int(step.total_seconds() // 60),
                "slots": [
                    {"start": s.astimezone(tz).isoformat(), "end": (s + step).astimezone(tz).isoformat()}
                    for s in free
                ],
            }
        )


class AppointmentCreateView(APIView):
    def post(self, request):
        data = BookAppointmentSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        appt = booking.book(
            doctor_id=data.validated_data["doctor_id"],
            patient_id=data.validated_data["patient_id"],
            start=data.validated_data["start_time"],
            notes=data.validated_data.get("notes", ""),
        )
        return _appointment_response(appt, status.HTTP_201_CREATED)


class AppointmentDetailView(APIView):
    def get(self, request, appointment_id: int):
        appt = get_object_or_404(Appointment.objects.select_related("doctor", "patient"), pk=appointment_id)
        return Response(AppointmentSerializer(appt).data)


class AppointmentCancelView(APIView):
    def patch(self, request, appointment_id: int):
        data = CancelSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        appt = booking.cancel(appointment_id=appointment_id, reason=data.validated_data["reason"])
        return _appointment_response(appt)


class AppointmentRescheduleView(APIView):
    def patch(self, request, appointment_id: int):
        data = RescheduleSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        appt = booking.reschedule(appointment_id=appointment_id, new_start=data.validated_data["start_time"])
        return _appointment_response(appt)


class PatientCreateView(APIView):
    def post(self, request):
        ser = PatientSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        patient = ser.save()
        return Response(PatientSerializer(patient).data, status=status.HTTP_201_CREATED)


class PatientDetailView(APIView):
    def get(self, request, patient_id: int):
        patient = get_object_or_404(Patient, pk=patient_id)
        return Response(PatientSerializer(patient).data)


class PatientAppointmentsView(APIView):
    def get(self, request, patient_id: int):
        patient = get_object_or_404(Patient, pk=patient_id)
        upcoming = (
            Appointment.objects.filter(
                patient=patient, status=Appointment.Status.BOOKED, start_time__gt=clock.now()
            )
            .select_related("doctor", "patient")
            .order_by("start_time")
        )
        return Response(AppointmentSerializer(upcoming, many=True).data)

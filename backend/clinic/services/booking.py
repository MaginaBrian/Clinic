from __future__ import annotations

from datetime import datetime

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound

from .. import clock
from ..exceptions import Conflict, InvalidSlot
from ..models import Appointment, Doctor, Patient
from . import slots


def _as_aware(value: datetime) -> datetime:
    if timezone.is_naive(value):
        return value.replace(tzinfo=slots.clinic_tz())
    return value


def validate_slot(doctor: Doctor, start: datetime, *, now: datetime, exclude: Appointment | None = None) -> None:
    local = start.astimezone(slots.clinic_tz())

    if start <= now:
        raise InvalidSlot("Appointments cannot be booked in the past.", "slot_in_past")

    if start < slots.earliest_bookable(now):
        raise InvalidSlot(
            f"Appointments must be booked at least {settings.MIN_BOOKING_LEAD_MINUTES} minutes in advance.",
            "too_soon",
        )

    if not slots.is_within_working_hours(doctor, start):
        raise InvalidSlot(
            f"{doctor.name} does not work at {local:%A %d %b %Y %H:%M}. Check /doctors/{doctor.pk}/availability for open slots.",
            "outside_working_hours",
        )

    if not slots.is_slot_start(doctor, start):
        raise InvalidSlot(
            f"{local:%H:%M} is not a valid slot start. Slots begin on the 30-minute grid of the doctor's working hours.",
            "misaligned_slot",
        )

    taken = Appointment.objects.filter(doctor=doctor, start_time=start, status=Appointment.Status.BOOKED)
    if exclude is not None:
        taken = taken.exclude(pk=exclude.pk)
    if taken.exists():
        raise Conflict("That slot has already been booked. Please choose another.", "slot_taken")


def _check_patient_free(patient: Patient, start: datetime, exclude: Appointment | None = None) -> None:
    clash = Appointment.objects.filter(patient=patient, start_time=start, status=Appointment.Status.BOOKED)
    if exclude is not None:
        clash = clash.exclude(pk=exclude.pk)
    if clash.exists():
        raise Conflict("The patient already has an appointment at that time.", "patient_double_booked")


def _get_doctor_locked(doctor_id: int) -> Doctor:
    try:
        return Doctor.objects.select_for_update().prefetch_related("working_hours").get(pk=doctor_id, is_active=True)
    except Doctor.DoesNotExist:
        raise NotFound("Doctor not found.", "doctor_not_found")


def book(*, doctor_id: int, patient_id: int, start: datetime, notes: str = "") -> Appointment:
    start = _as_aware(start)
    with transaction.atomic():
        doctor = _get_doctor_locked(doctor_id)
        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            raise NotFound("Patient not found.", "patient_not_found")

        validate_slot(doctor, start, now=clock.now())
        _check_patient_free(patient, start)
        try:
            with transaction.atomic():
                return Appointment.objects.create(
                    doctor=doctor,
                    patient=patient,
                    start_time=start,
                    end_time=start + slots.slot_length(),
                    notes=notes,
                )
        except IntegrityError:
            raise Conflict("That slot has just been booked by someone else.", "slot_taken")


def _get_appointment_locked(appointment_id: int) -> Appointment:
    qs = Appointment.objects.select_for_update().select_related("doctor", "patient")
    try:
        return qs.get(pk=appointment_id)
    except Appointment.DoesNotExist:
        raise NotFound("Appointment not found.", "appointment_not_found")


def cancel(*, appointment_id: int, reason: str) -> Appointment:
    with transaction.atomic():
        appt = _get_appointment_locked(appointment_id)
        if appt.status == Appointment.Status.CANCELLED:
            raise Conflict("This appointment is already cancelled.", "already_cancelled")
        if appt.start_time <= clock.now():
            raise InvalidSlot("Appointments that have already started cannot be cancelled.", "appointment_in_past")
        appt.status = Appointment.Status.CANCELLED
        appt.cancel_reason = reason
        appt.cancelled_at = clock.now()
        appt.save(update_fields=["status", "cancel_reason", "cancelled_at", "updated_at"])
        return appt


def reschedule(*, appointment_id: int, new_start: datetime) -> Appointment:
    new_start = _as_aware(new_start)
    with transaction.atomic():
        try:
            doctor_id = Appointment.objects.values_list("doctor_id", flat=True).get(pk=appointment_id)
        except Appointment.DoesNotExist:
            raise NotFound("Appointment not found.", "appointment_not_found")
        doctor = _get_doctor_locked(doctor_id)
        appt = _get_appointment_locked(appointment_id)

        if appt.status == Appointment.Status.CANCELLED:
            raise Conflict("A cancelled appointment cannot be rescheduled. Book a new one instead.", "already_cancelled")
        now = clock.now()
        if appt.start_time <= now:
            raise InvalidSlot("Appointments that have already started cannot be rescheduled.", "appointment_in_past")
        if new_start == appt.start_time:
            raise InvalidSlot("The appointment is already at that time.", "same_slot")

        validate_slot(doctor, new_start, now=now, exclude=appt)
        _check_patient_free(appt.patient, new_start, exclude=appt)
        appt.start_time = new_start
        appt.end_time = new_start + slots.slot_length()
        try:
            with transaction.atomic():
                appt.save(update_fields=["start_time", "end_time", "updated_at"])
        except IntegrityError:
            raise Conflict("That slot has just been booked by someone else.", "slot_taken")
        return appt

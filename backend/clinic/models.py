from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Doctor(models.Model):
    name = models.CharField(max_length=120)
    specialty = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkingHours(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0
        TUESDAY = 1
        WEDNESDAY = 2
        THURSDAY = 3
        FRIDAY = 4
        SATURDAY = 5
        SUNDAY = 6

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="working_hours")
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["doctor_id", "weekday", "start_time"]
        verbose_name_plural = "working hours"
        constraints = [
            models.CheckConstraint(condition=Q(start_time__lt=models.F("end_time")), name="working_hours_start_before_end"),
            models.UniqueConstraint(fields=["doctor", "weekday", "start_time"], name="uniq_working_block"),
        ]

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("start_time must be before end_time.")
        if self.doctor_id and self.start_time and self.end_time:
            overlapping = (
                WorkingHours.objects.filter(doctor_id=self.doctor_id, weekday=self.weekday)
                .exclude(pk=self.pk)
                .filter(start_time__lt=self.end_time, end_time__gt=self.start_time)
            )
            if overlapping.exists():
                raise ValidationError("This block overlaps another working block for the same doctor and weekday.")

    def __str__(self):
        return f"{self.doctor} {self.get_weekday_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"


class Patient(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Appointment(models.Model):
    class Status(models.TextChoices):
        BOOKED = "booked", "Booked"
        CANCELLED = "cancelled", "Cancelled"

    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name="appointments")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="appointments")
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.BOOKED)
    notes = models.CharField(max_length=500, blank=True)
    cancel_reason = models.CharField(max_length=500, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "start_time"],
                condition=Q(status="booked"),
                name="uniq_booked_slot_per_doctor",
            ),
            models.CheckConstraint(condition=Q(start_time__lt=models.F("end_time")), name="appointment_start_before_end"),
        ]
        indexes = [models.Index(fields=["patient", "status", "start_time"], name="appt_patient_upcoming_idx")]

    def __str__(self):
        return f"{self.patient} with {self.doctor} @ {self.start_time:%Y-%m-%d %H:%M} ({self.status})"

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from ..models import Appointment, Doctor


def clinic_tz() -> ZoneInfo:
    return ZoneInfo(settings.TIME_ZONE)


def slot_length() -> timedelta:
    return timedelta(minutes=settings.CLINIC_SLOT_MINUTES)


def windows_for_day(doctor: Doctor, day: date) -> list[tuple[datetime, datetime]]:
    tz = clinic_tz()
    blocks = [wh for wh in doctor.working_hours.all() if wh.weekday == day.weekday()]
    blocks.sort(key=lambda wh: wh.start_time)
    return [
        (datetime.combine(day, wh.start_time, tzinfo=tz), datetime.combine(day, wh.end_time, tzinfo=tz))
        for wh in blocks
    ]


def all_slots_for_day(doctor: Doctor, day: date) -> list[datetime]:
    step = slot_length()
    starts: list[datetime] = []
    for window_start, window_end in windows_for_day(doctor, day):
        cursor = window_start
        while cursor + step <= window_end:
            starts.append(cursor)
            cursor += step
    return starts


def is_within_working_hours(doctor: Doctor, start: datetime) -> bool:
    local = start.astimezone(clinic_tz())
    end = local + slot_length()
    return any(ws <= local and end <= we for ws, we in windows_for_day(doctor, local.date()))


def is_slot_start(doctor: Doctor, start: datetime) -> bool:
    local = start.astimezone(clinic_tz())
    return local in all_slots_for_day(doctor, local.date())


def earliest_bookable(now: datetime) -> datetime:
    return now + timedelta(minutes=settings.MIN_BOOKING_LEAD_MINUTES)


def available_slots(doctor: Doctor, day: date, now: datetime) -> list[datetime]:
    tz = clinic_tz()
    day_start = datetime.combine(day, datetime.min.time(), tzinfo=tz)
    booked = set(
        Appointment.objects.filter(
            doctor=doctor,
            status=Appointment.Status.BOOKED,
            start_time__gte=day_start,
            start_time__lt=day_start + timedelta(days=1),
        ).values_list("start_time", flat=True)
    )
    cutoff = earliest_bookable(now)
    return [s for s in all_slots_for_day(doctor, day) if s not in booked and s >= cutoff]

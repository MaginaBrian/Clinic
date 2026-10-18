from datetime import datetime, time
from unittest.mock import patch
from zoneinfo import ZoneInfo

from rest_framework.test import APITestCase

from clinic.models import Doctor, Patient, WorkingHours

NAIROBI = ZoneInfo("Africa/Nairobi")


def nairobi(y, m, d, hh=0, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=NAIROBI)


NOW = nairobi(2026, 11, 2, 8, 0)
MONDAY = "2026-11-02"
TUESDAY = "2026-11-03"
SATURDAY = "2026-11-07"


class ClinicTestCase(APITestCase):
    def setUp(self):
        patcher = patch("clinic.clock.now", return_value=NOW)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.doctor = Doctor.objects.create(name="Dr. Test", specialty="GP")
        self.other_doctor = Doctor.objects.create(name="Dr. Other")
        for doc in (self.doctor, self.other_doctor):
            for wd in range(0, 5):
                WorkingHours.objects.create(doctor=doc, weekday=wd, start_time=time(9), end_time=time(12))
                WorkingHours.objects.create(doctor=doc, weekday=wd, start_time=time(13), end_time=time(17))
        self.patient = Patient.objects.create(name="Wanjiru", phone="0712345678")
        self.patient2 = Patient.objects.create(name="Otieno", phone="0722345678")

    def book(self, start, doctor=None, patient=None):
        return self.client.post(
            "/appointments",
            {
                "doctor_id": (doctor or self.doctor).pk,
                "patient_id": (patient or self.patient).pk,
                "start_time": start if isinstance(start, str) else start.isoformat(),
            },
            format="json",
        )

    def availability(self, day, doctor=None):
        r = self.client.get(f"/doctors/{(doctor or self.doctor).pk}/availability", {"date": day})
        return r

    def slot_starts(self, day, doctor=None):
        return [s["start"] for s in self.availability(day, doctor).json()["slots"]]

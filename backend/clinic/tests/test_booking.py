from datetime import timedelta

from django.db import IntegrityError, transaction

from clinic.models import Appointment

from .base import NOW, ClinicTestCase, nairobi


class BookingTests(ClinicTestCase):
    def test_books_a_valid_slot(self):
        r = self.book(nairobi(2026, 11, 3, 10, 0))
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body["status"], "booked")
        self.assertEqual(body["start_time"], "2026-11-03T10:00:00+03:00")
        self.assertEqual(body["end_time"], "2026-11-03T10:30:00+03:00")
        self.assertEqual(body["doctor"]["id"], self.doctor.pk)

    def test_equivalent_instants_in_other_timezones_are_the_same_slot(self):
        self.assertEqual(self.book("2026-11-03T07:00:00Z").status_code, 201)
        r = self.book("2026-11-03T10:00:00+03:00")
        self.assertEqual(r.status_code, 409)

    def test_offset_less_datetime_is_read_as_clinic_time(self):
        r = self.book("2026-11-03T10:00:00")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["start_time"], "2026-11-03T10:00:00+03:00")

    def test_double_booking_is_rejected_with_409(self):
        self.assertEqual(self.book(nairobi(2026, 11, 3, 10, 0)).status_code, 201)
        r = self.book(nairobi(2026, 11, 3, 10, 0), patient=self.patient2)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()["error"]["code"], "slot_taken")

    def test_same_time_with_a_different_doctor_is_fine(self):
        self.assertEqual(self.book(nairobi(2026, 11, 3, 10, 0)).status_code, 201)
        self.assertEqual(self.book(nairobi(2026, 11, 3, 10, 0), doctor=self.other_doctor, patient=self.patient2).status_code, 201)

    def test_patient_cannot_be_in_two_places_at_once(self):
        self.book(nairobi(2026, 11, 3, 10, 0))
        r = self.book(nairobi(2026, 11, 3, 10, 0), doctor=self.other_doctor)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()["error"]["code"], "patient_double_booked")

    def test_rejects_slots_in_the_past(self):
        r = self.book(NOW - timedelta(days=1))
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "slot_in_past")

    def test_rejects_slots_within_one_hour(self):
        r = self.book(nairobi(2026, 11, 2, 8, 30))
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "too_soon")

    def test_allows_exactly_one_hour_ahead(self):
        self.assertEqual(self.book(nairobi(2026, 11, 2, 9, 0)).status_code, 201)

    def test_rejects_outside_working_hours(self):
        for hh, mm in [(7, 0), (12, 0), (12, 30), (16, 45), (17, 0), (20, 0)]:
            with self.subTest(time=f"{hh}:{mm:02d}"):
                r = self.book(nairobi(2026, 11, 3, hh, mm), patient=self.patient2)
                self.assertEqual(r.status_code, 400, r.content)
                self.assertEqual(r.json()["error"]["code"], "outside_working_hours")

    def test_last_slot_before_close_is_bookable(self):
        self.assertEqual(self.book(nairobi(2026, 11, 3, 16, 30)).status_code, 201)

    def test_rejects_non_working_day(self):
        r = self.book(nairobi(2026, 11, 7, 10, 0))
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "outside_working_hours")

    def test_rejects_misaligned_start(self):
        r = self.book(nairobi(2026, 11, 3, 10, 15))
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "misaligned_slot")

    def test_validation_errors(self):
        r = self.client.post("/appointments", {"doctor_id": "x"}, format="json")
        self.assertEqual(r.status_code, 400)
        details = r.json()["error"]["details"]
        self.assertIn("doctor_id", details)
        self.assertIn("patient_id", details)
        self.assertIn("start_time", details)

    def test_unknown_doctor_or_patient_is_404(self):
        r = self.client.post("/appointments", {"doctor_id": 999, "patient_id": self.patient.pk, "start_time": "2026-11-03T10:00:00"}, format="json")
        self.assertEqual(r.status_code, 404)
        r = self.client.post("/appointments", {"doctor_id": self.doctor.pk, "patient_id": 999, "start_time": "2026-11-03T10:00:00"}, format="json")
        self.assertEqual(r.status_code, 404)

    def test_database_constraint_is_the_backstop_against_double_booking(self):
        start = nairobi(2026, 11, 3, 10, 0)
        kwargs = dict(doctor=self.doctor, patient=self.patient, start_time=start, end_time=start + timedelta(minutes=30))
        Appointment.objects.create(**kwargs)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Appointment.objects.create(**{**kwargs, "patient": self.patient2})

    def test_constraint_ignores_cancelled_rows(self):
        start = nairobi(2026, 11, 3, 10, 0)
        kwargs = dict(doctor=self.doctor, patient=self.patient, start_time=start, end_time=start + timedelta(minutes=30))
        Appointment.objects.create(**kwargs, status="cancelled")
        Appointment.objects.create(**kwargs, status="cancelled")
        Appointment.objects.create(**kwargs)

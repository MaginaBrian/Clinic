from clinic.models import Appointment

from .base import ClinicTestCase, nairobi

TEN = nairobi(2026, 11, 3, 10, 0)
ELEVEN = nairobi(2026, 11, 3, 11, 0)


class CancelTests(ClinicTestCase):
    def setUp(self):
        super().setUp()
        self.appt_id = self.book(TEN).json()["id"]

    def cancel(self, reason="Feeling better", appt_id=None):
        return self.client.patch(f"/appointments/{appt_id or self.appt_id}/cancel", {"reason": reason}, format="json")

    def test_cancel_stores_reason_and_frees_the_slot(self):
        r = self.cancel("Travelling")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "cancelled")
        self.assertEqual(r.json()["cancel_reason"], "Travelling")
        self.assertIsNotNone(r.json()["cancelled_at"])
        self.assertIn("2026-11-03T10:00:00+03:00", self.slot_starts("2026-11-03"))

    def test_slot_can_be_rebooked_after_cancel(self):
        self.cancel()
        self.assertEqual(self.book(TEN, patient=self.patient2).status_code, 201)

    def test_cancelling_twice_is_409(self):
        self.cancel()
        r = self.cancel()
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()["error"]["code"], "already_cancelled")

    def test_reason_is_required(self):
        for body in ({}, {"reason": ""}, {"reason": "  "}):
            r = self.client.patch(f"/appointments/{self.appt_id}/cancel", body, format="json")
            self.assertEqual(r.status_code, 400, body)
        self.assertEqual(Appointment.objects.get(pk=self.appt_id).status, "booked")

    def test_unknown_appointment_404(self):
        self.assertEqual(self.cancel(appt_id=9999).status_code, 404)

    def test_cannot_cancel_an_appointment_that_already_started(self):
        past = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            start_time=nairobi(2026, 11, 2, 7, 0), end_time=nairobi(2026, 11, 2, 7, 30),
        )
        r = self.cancel(appt_id=past.pk)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "appointment_in_past")


class RescheduleTests(ClinicTestCase):
    def setUp(self):
        super().setUp()
        self.appt_id = self.book(TEN).json()["id"]

    def reschedule(self, start, appt_id=None):
        return self.client.patch(
            f"/appointments/{appt_id or self.appt_id}/reschedule",
            {"start_time": start.isoformat()},
            format="json",
        )

    def test_moves_appointment_and_swaps_availability(self):
        r = self.reschedule(ELEVEN)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["start_time"], "2026-11-03T11:00:00+03:00")
        self.assertEqual(r.json()["id"], self.appt_id)
        starts = self.slot_starts("2026-11-03")
        self.assertIn("2026-11-03T10:00:00+03:00", starts)
        self.assertNotIn("2026-11-03T11:00:00+03:00", starts)

    def test_new_slot_gets_full_validation(self):
        cases = {
            "outside_working_hours": nairobi(2026, 11, 3, 12, 30),
            "slot_in_past": nairobi(2026, 11, 1, 10, 0),
            "too_soon": nairobi(2026, 11, 2, 8, 30),
            "misaligned_slot": nairobi(2026, 11, 3, 10, 45),
        }
        for code, when in cases.items():
            with self.subTest(code=code):
                r = self.reschedule(when)
                self.assertEqual(r.status_code, 400, r.content)
                self.assertEqual(r.json()["error"]["code"], code)
        self.assertEqual(Appointment.objects.get(pk=self.appt_id).start_time, TEN)

    def test_cannot_move_onto_a_taken_slot(self):
        self.book(ELEVEN, patient=self.patient2)
        r = self.reschedule(ELEVEN)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()["error"]["code"], "slot_taken")
        self.assertEqual(Appointment.objects.get(pk=self.appt_id).start_time, TEN)

    def test_cancelled_appointment_cannot_be_rescheduled(self):
        self.client.patch(f"/appointments/{self.appt_id}/cancel", {"reason": "Changed my mind"}, format="json")
        r = self.reschedule(ELEVEN)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()["error"]["code"], "already_cancelled")

    def test_same_slot_is_rejected(self):
        r = self.reschedule(TEN)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "same_slot")

    def test_can_move_into_a_slot_freed_by_someone_elses_cancellation(self):
        other = self.book(ELEVEN, patient=self.patient2).json()["id"]
        self.client.patch(f"/appointments/{other}/cancel", {"reason": "Sick"}, format="json")
        self.assertEqual(self.reschedule(ELEVEN).status_code, 200)

    def test_unknown_appointment_404(self):
        self.assertEqual(self.reschedule(ELEVEN, appt_id=9999).status_code, 404)

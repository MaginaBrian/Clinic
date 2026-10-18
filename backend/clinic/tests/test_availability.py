from .base import MONDAY, SATURDAY, TUESDAY, ClinicTestCase, nairobi


class AvailabilityTests(ClinicTestCase):
    def test_lists_30_minute_slots_across_both_working_blocks(self):
        starts = self.slot_starts(TUESDAY)
        self.assertEqual(len(starts), 6 + 8)
        self.assertEqual(starts[0], "2026-11-03T09:00:00+03:00")
        self.assertEqual(starts[5], "2026-11-03T11:30:00+03:00")
        self.assertEqual(starts[6], "2026-11-03T13:00:00+03:00")

    def test_response_shape(self):
        body = self.availability(TUESDAY).json()
        self.assertEqual(body["slot_minutes"], 30)
        self.assertEqual(body["timezone"], "Africa/Nairobi")
        self.assertEqual(body["slots"][0]["end"], "2026-11-03T09:30:00+03:00")

    def test_non_working_day_is_empty_not_an_error(self):
        r = self.availability(SATURDAY)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["slots"], [])

    def test_booked_slot_disappears(self):
        self.assertEqual(self.book(nairobi(2026, 11, 3, 10, 0)).status_code, 201)
        self.assertNotIn("2026-11-03T10:00:00+03:00", self.slot_starts(TUESDAY))
        self.assertEqual(len(self.slot_starts(TUESDAY)), 13)

    def test_booking_one_doctor_does_not_affect_another(self):
        self.book(nairobi(2026, 11, 3, 10, 0))
        self.assertIn("2026-11-03T10:00:00+03:00", self.slot_starts(TUESDAY, self.other_doctor))

    def test_past_and_too_soon_slots_are_not_offered(self):
        starts = self.slot_starts(MONDAY)
        self.assertEqual(starts[0], "2026-11-02T09:00:00+03:00")
        self.assertEqual(self.slot_starts("2026-11-01"), [])

    def test_requires_valid_date(self):
        r = self.client.get(f"/doctors/{self.doctor.pk}/availability")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "validation_error")
        r = self.client.get(f"/doctors/{self.doctor.pk}/availability", {"date": "02/11/2026"})
        self.assertEqual(r.status_code, 400)

    def test_unknown_doctor_404(self):
        r = self.client.get("/doctors/9999/availability", {"date": TUESDAY})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["error"]["code"], "doctor_not_found")

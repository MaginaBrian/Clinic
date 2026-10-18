from .base import ClinicTestCase, nairobi


class PatientTests(ClinicTestCase):
    def test_create_patient(self):
        r = self.client.post("/patients", {"name": "Achieng", "phone": "+254 700 111 222"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertIn("id", r.json())

    def test_rejects_bad_phone(self):
        r = self.client.post("/patients", {"name": "Achieng", "phone": "123"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("phone", r.json()["error"]["details"])

    def test_upcoming_appointments_sorted_by_date_and_exclude_cancelled(self):
        later = self.book(nairobi(2026, 11, 5, 14, 0)).json()["id"]
        sooner = self.book(nairobi(2026, 11, 3, 10, 0)).json()["id"]
        cancelled = self.book(nairobi(2026, 11, 4, 10, 0)).json()["id"]
        self.client.patch(f"/appointments/{cancelled}/cancel", {"reason": "Clash"}, format="json")
        self.book(nairobi(2026, 11, 3, 15, 0), patient=self.patient2)

        r = self.client.get(f"/patients/{self.patient.pk}/appointments")
        self.assertEqual(r.status_code, 200)
        self.assertEqual([a["id"] for a in r.json()], [sooner, later])

    def test_unknown_patient_404(self):
        self.assertEqual(self.client.get("/patients/999/appointments").status_code, 404)

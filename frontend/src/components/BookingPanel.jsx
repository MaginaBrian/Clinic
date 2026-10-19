import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useAvailability } from "../hooks.js";
import { formatLongDate, formatTime, todayKey } from "../time.js";
import DateStrip from "./DateStrip.jsx";
import DaySheet from "./DaySheet.jsx";

export default function BookingPanel({ patient, doctors, onBooked, version }) {
  const [doctorId, setDoctorId] = useState(null);
  const [date, setDate] = useState(todayKey());
  const [slot, setSlot] = useState(null);
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!doctorId && doctors.length) setDoctorId(doctors[0].id);
  }, [doctors, doctorId]);

  const availability = useAvailability(doctorId, date, version);
  const doctor = doctors.find((d) => d.id === doctorId);

  const pick = (setter) => (value) => {
    setter(value);
    setSlot(null);
    setError(null);
  };

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      const appt = await api.book({
        doctor_id: doctorId,
        patient_id: patient.id,
        start_time: slot.start,
        notes: notes.trim(),
      });
      setSlot(null);
      setNotes("");
      onBooked(appt);
    } catch (e) {
      setError(e.message);
      if (e.status === 409 || e.status === 400) {
        setSlot(null);
        availability.reload();
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel" aria-labelledby="book-h">
      <h2 id="book-h">Book an appointment</h2>

      <div className="doctor-list" role="radiogroup" aria-label="Choose a doctor">
        {doctors.map((d) => (
          <button
            key={d.id}
            type="button"
            role="radio"
            aria-checked={d.id === doctorId}
            className={`doctor${d.id === doctorId ? " is-selected" : ""}`}
            onClick={() => pick(setDoctorId)(d.id)}
          >
            <strong>{d.name}</strong>
            <span>{d.specialty}</span>
          </button>
        ))}
      </div>

      <DateStrip value={date} onChange={pick(setDate)} />
      <DaySheet
        slots={availability.slots}
        loading={availability.loading}
        error={availability.error}
        selected={slot?.start}
        onSelect={(s) => { setSlot(s); setError(null); }}
      />

      {slot && (
        <div className="confirm" role="region" aria-label="Confirm booking" aria-live="polite">
          <p>
            <strong>{formatTime(slot.start)}</strong> on {formatLongDate(slot.start)} with <strong>{doctor?.name}</strong>
          </p>
          <label>
            Reason for visit <span className="muted">(optional)</span>
            <input value={notes} maxLength={500} onChange={(e) => setNotes(e.target.value)} placeholder="e.g. Cough for two weeks" />
          </label>
          <button className="btn btn--primary" onClick={confirm} disabled={busy}>
            {busy ? "Booking…" : "Book this time"}
          </button>
        </div>
      )}
      {error && <p className="note note--error" role="alert">{error}</p>}
    </section>
  );
}

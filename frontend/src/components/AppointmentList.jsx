import { useState } from "react";
import { api } from "../api.js";
import { useAvailability } from "../hooks.js";
import { dayKey, formatLongDate, formatTime, todayKey } from "../time.js";
import DateStrip from "./DateStrip.jsx";
import DaySheet from "./DaySheet.jsx";

function CancelForm({ appt, onDone, onClose }) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.cancel(appt.id, reason.trim());
      onDone("Appointment cancelled. The time is free for others.");
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <form className="inline-form" onSubmit={submit}>
      <label>
        Why are you cancelling?
        <input required minLength={3} maxLength={500} value={reason} onChange={(e) => setReason(e.target.value)} autoFocus />
      </label>
      {error && <p className="note note--error" role="alert">{error}</p>}
      <div className="row">
        <button className="btn btn--danger" disabled={busy}>{busy ? "Cancelling…" : "Cancel appointment"}</button>
        <button type="button" className="btn" onClick={onClose}>Keep it</button>
      </div>
    </form>
  );
}

function RescheduleForm({ appt, onDone, onClose }) {
  const [date, setDate] = useState(dayKey(appt.start_time) >= todayKey() ? dayKey(appt.start_time) : todayKey());
  const [slot, setSlot] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const availability = useAvailability(appt.doctor.id, date);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await api.reschedule(appt.id, slot.start);
      onDone(`Moved to ${formatLongDate(slot.start)}, ${formatTime(slot.start)}.`);
    } catch (err) {
      setError(err.message);
      setSlot(null);
      availability.reload();
      setBusy(false);
    }
  }

  return (
    <div className="inline-form">
      <p className="muted">Pick a new time with {appt.doctor.name}.</p>
      <DateStrip value={date} onChange={(d) => { setDate(d); setSlot(null); }} />
      <DaySheet {...availability} selected={slot?.start} onSelect={setSlot} />
      {error && <p className="note note--error" role="alert">{error}</p>}
      <div className="row">
        <button className="btn btn--primary" disabled={!slot || busy} onClick={submit}>
          {busy ? "Moving…" : slot ? `Move to ${formatTime(slot.start)}` : "Choose a time"}
        </button>
        <button type="button" className="btn" onClick={onClose}>Close</button>
      </div>
    </div>
  );
}

export default function AppointmentList({ appointments, loading, error, onChanged }) {
  const [open, setOpen] = useState(null);
  const finish = (message) => { setOpen(null); onChanged(message); };

  return (
    <section className="panel" aria-labelledby="mine-h">
      <h2 id="mine-h">Your upcoming appointments</h2>
      {error && <p className="note note--error" role="alert">{error}</p>}
      {!error && loading && appointments.length === 0 && <p className="note">Loading…</p>}
      {!loading && !error && appointments.length === 0 && (
        <p className="note">Nothing booked yet. Pick a doctor and a time to get started.</p>
      )}
      <ul className="appts">
        {appointments.map((a) => {
          const isOpen = open?.id === a.id;
          return (
            <li key={a.id} className="appt">
              <div className="appt__when">
                <strong>{formatTime(a.start_time)}</strong>
                <span>{formatLongDate(a.start_time)}</span>
              </div>
              <div className="appt__who">
                {a.doctor.name}
                {a.notes && <span className="muted"> · {a.notes}</span>}
              </div>
              {!isOpen && (
                <div className="row">
                  <button className="btn btn--small" onClick={() => setOpen({ id: a.id, mode: "reschedule" })}>Reschedule</button>
                  <button className="btn btn--small btn--quiet" onClick={() => setOpen({ id: a.id, mode: "cancel" })}>Cancel</button>
                </div>
              )}
              {isOpen && open.mode === "cancel" && <CancelForm appt={a} onDone={finish} onClose={() => setOpen(null)} />}
              {isOpen && open.mode === "reschedule" && <RescheduleForm appt={a} onDone={finish} onClose={() => setOpen(null)} />}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

import { useState } from "react";
import { api } from "../api.js";

export default function PatientGate({ onReady }) {
  const [form, setForm] = useState({ name: "", phone: "", email: "" });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      onReady(await api.createPatient({ ...form, name: form.name.trim() }));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="panel gate" onSubmit={submit}>
      <h2>Who is this appointment for?</h2>
      <p className="muted">We'll keep your bookings on this device so you can move or cancel them later.</p>
      <label>
        Full name
        <input required minLength={2} value={form.name} onChange={set("name")} autoComplete="name" />
      </label>
      <label>
        Phone number
        <input required type="tel" value={form.phone} onChange={set("phone")} autoComplete="tel" placeholder="0712 345 678" />
      </label>
      <label>
        Email <span className="muted">(optional)</span>
        <input type="email" value={form.email} onChange={set("email")} autoComplete="email" />
      </label>
      {error && <p className="note note--error" role="alert">{error}</p>}
      <button className="btn btn--primary" disabled={busy}>{busy ? "Saving…" : "Continue"}</button>
    </form>
  );
}

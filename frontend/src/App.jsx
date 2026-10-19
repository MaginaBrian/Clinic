import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import AppointmentList from "./components/AppointmentList.jsx";
import BookingPanel from "./components/BookingPanel.jsx";
import PatientGate from "./components/PatientGate.jsx";
import { formatLongDate, formatTime } from "./time.js";

const STORAGE_KEY = "clinic.patientId";

export default function App() {
  const [patient, setPatient] = useState(null);
  const [booting, setBooting] = useState(true);
  const [doctors, setDoctors] = useState([]);
  const [appts, setAppts] = useState({ list: [], loading: false, error: null });
  const [toast, setToast] = useState(null);
  const [fatal, setFatal] = useState(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    (async () => {
      try {
        setDoctors(await api.doctors());
        const id = localStorage.getItem(STORAGE_KEY);
        if (id) setPatient(await api.getPatient(id).catch(() => null));
      } catch (e) {
        setFatal(e.message);
      } finally {
        setBooting(false);
      }
    })();
  }, []);

  const refresh = useCallback(async () => {
    if (!patient) return;
    setAppts((s) => ({ ...s, loading: true, error: null }));
    try {
      setAppts({ list: await api.upcoming(patient.id), loading: false, error: null });
    } catch (e) {
      setAppts({ list: [], loading: false, error: e.message });
    }
  }, [patient]);

  useEffect(() => { refresh(); }, [refresh]);
  const changed = (message) => { setToast(message); setVersion((v) => v + 1); refresh(); };

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 5000);
    return () => clearTimeout(t);
  }, [toast]);

  const ready = (p) => { localStorage.setItem(STORAGE_KEY, p.id); setPatient(p); };
  const signOut = () => { localStorage.removeItem(STORAGE_KEY); setPatient(null); setAppts({ list: [], loading: false, error: null }); };

  return (
    <>
      <header className="masthead">
        <div>
          <h1>Mwangaza Clinic</h1>
          <p>Book a visit in under a minute. Times are shown in Nairobi time.</p>
        </div>
        {patient && (
          <p className="masthead__who">
            {patient.name} <button className="link" onClick={signOut}>Not you?</button>
          </p>
        )}
      </header>

      <main>
        {fatal && <p className="note note--error" role="alert">{fatal}</p>}
        {booting && !fatal && <p className="note">Loading…</p>}
        {!booting && !fatal && !patient && <PatientGate onReady={ready} />}
        {!booting && !fatal && patient && (
          <div className="layout">
            <BookingPanel
              patient={patient}
              doctors={doctors}
              version={version}
              onBooked={(a) => changed(`Booked: ${formatLongDate(a.start_time)} at ${formatTime(a.start_time)} with ${a.doctor.name}.`)}
            />
            <AppointmentList
              appointments={appts.list}
              loading={appts.loading}
              error={appts.error}
              onChanged={changed}
            />
          </div>
        )}
      </main>

      {toast && <div className="toast" role="status">{toast}</div>}
    </>
  );
}

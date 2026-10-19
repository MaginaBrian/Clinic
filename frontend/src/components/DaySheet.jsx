import { formatHour, minutesPart } from "../time.js";

export default function DaySheet({ slots, loading, error, selected, onSelect }) {
  if (error) return <p className="note note--error" role="alert">{error}</p>;
  if (loading && slots.length === 0) return <p className="note" aria-live="polite">Loading free times…</p>;
  if (slots.length === 0) {
    return <p className="note">No free times on this day. Try another day.</p>;
  }

  const rows = [];
  for (const slot of slots) {
    const label = formatHour(slot.start);
    const last = rows[rows.length - 1];
    if (last && last.label === label) last.slots.push(slot);
    else rows.push({ label, slots: [slot] });
  }

  return (
    <ol className={`sheet${loading ? " is-stale" : ""}`} aria-label="Free times">
      {rows.map((row) => (
        <li key={row.label} className="sheet__row">
          <span className="sheet__hour">{row.label}</span>
          <span className="sheet__slots">
            {row.slots.map((s) => (
              <button
                key={s.start}
                type="button"
                className={`slot${selected === s.start ? " is-selected" : ""}`}
                aria-pressed={selected === s.start}
                onClick={() => onSelect(s)}
              >
                :{minutesPart(s.start)}
              </button>
            ))}
          </span>
        </li>
      ))}
    </ol>
  );
}

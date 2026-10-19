import { addDays, dayParts, todayKey } from "../time.js";

const DAYS_AHEAD = 14;

export default function DateStrip({ value, onChange }) {
  const today = todayKey();
  const days = Array.from({ length: DAYS_AHEAD }, (_, i) => addDays(today, i));
  return (
    <div className="date-strip" role="group" aria-label="Choose a day">
      {days.map((key) => {
        const { weekday, day, month } = dayParts(key);
        const selected = key === value;
        return (
          <button
            key={key}
            type="button"
            className={`date-chip${selected ? " is-selected" : ""}`}
            aria-pressed={selected}
            onClick={() => onChange(key)}
          >
            <span className="date-chip__weekday">{key === today ? "Today" : weekday}</span>
            <span className="date-chip__day">{day}</span>
            <span className="date-chip__month">{month}</span>
          </button>
        );
      })}
    </div>
  );
}

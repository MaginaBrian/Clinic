export const CLINIC_TZ = "Africa/Nairobi";

const fmt = (opts) => new Intl.DateTimeFormat("en-GB", { timeZone: CLINIC_TZ, ...opts });
const timeFmt = fmt({ hour: "numeric", minute: "2-digit", hour12: true });
const hourFmt = fmt({ hour: "numeric", hour12: true });
const longDate = fmt({ weekday: "long", day: "numeric", month: "long" });

export const formatTime = (iso) => timeFmt.format(new Date(iso)).replace(/\s/g, "\u202f").toLowerCase();
export const formatHour = (iso) => hourFmt.format(new Date(iso)).replace(/\s/g, "\u202f").toLowerCase();
export const formatLongDate = (isoOrDate) => longDate.format(new Date(isoOrDate));
export const minutesPart = (iso) => timeFmt.formatToParts(new Date(iso)).find((p) => p.type === "minute").value;
export const dayKey = (iso) => new Intl.DateTimeFormat("en-CA", { timeZone: CLINIC_TZ }).format(new Date(iso));
export const todayKey = () => dayKey(new Date().toISOString());

export function addDays(key, n) {
  const d = new Date(`${key}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

export function dayParts(key) {
  const d = new Date(`${key}T12:00:00Z`);
  const p = (o) => new Intl.DateTimeFormat("en-GB", { timeZone: "UTC", ...o }).format(d);
  return { weekday: p({ weekday: "short" }), day: p({ day: "numeric" }), month: p({ month: "short" }) };
}

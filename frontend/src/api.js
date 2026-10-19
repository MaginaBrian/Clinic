export class ApiError extends Error {
  constructor(status, code, message, details) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request(path, { method = "GET", body, params } = {}) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  let res;
  try {
    res = await fetch(path + qs, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "network", "Can't reach the server. Check your connection and try again.");
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = data?.error;
    let message = err?.message || "Something went wrong. Please try again.";
    if (err?.details) {
      const first = Object.entries(err.details)[0];
      if (first) message = `${first[0].replace(/_/g, " ")}: ${[].concat(first[1])[0]}`;
    }
    throw new ApiError(res.status, err?.code || "error", message, err?.details);
  }
  return data;
}

export const api = {
  doctors: () => request("/doctors"),
  availability: (doctorId, date) => request(`/doctors/${doctorId}/availability`, { params: { date } }),
  createPatient: (patient) => request("/patients", { method: "POST", body: patient }),
  getPatient: (id) => request(`/patients/${id}`),
  upcoming: (patientId) => request(`/patients/${patientId}/appointments`),
  book: (payload) => request("/appointments", { method: "POST", body: payload }),
  cancel: (id, reason) => request(`/appointments/${id}/cancel`, { method: "PATCH", body: { reason } }),
  reschedule: (id, startTime) => request(`/appointments/${id}/reschedule`, { method: "PATCH", body: { start_time: startTime } }),
};

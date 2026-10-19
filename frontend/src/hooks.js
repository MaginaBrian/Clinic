import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api.js";

export function useAvailability(doctorId, date, version = 0) {
  const [state, setState] = useState({ slots: [], loading: false, error: null });
  const reqId = useRef(0);

  const load = useCallback(async () => {
    if (!doctorId || !date) return;
    const id = ++reqId.current;
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await api.availability(doctorId, date);
      if (id === reqId.current) setState({ slots: data.slots, loading: false, error: null });
    } catch (e) {
      if (id === reqId.current) setState({ slots: [], loading: false, error: e.message });
    }
  }, [doctorId, date, version]);

  useEffect(() => {
    load();
  }, [load]);

  return { ...state, reload: load };
}

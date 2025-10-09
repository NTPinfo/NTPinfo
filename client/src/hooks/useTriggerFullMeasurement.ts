import { useState } from "react";
import axios from "axios";

export const useTriggerMeasurement = () => {
  const [measurementId, setMeasurementId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [httpStatus, setHttpStatus] = useState<number>(200)
  const triggerMeasurement = async (
    endpoint: string,
    payload: { server: string; ipv6_measurement: boolean }
  ) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await axios.post(endpoint, payload, {
        headers: { "Content-Type": "application/json" },
      });
      const id = resp.data?.id;
      const status = resp.data?.status;
      setMeasurementId(id);
      setStatus(status);
      return { id, status: status };
    } catch (err: any) {
        console.warn(err);
        setError(err.response?.data?.detail || "Unknown error");
        setHttpStatus(err.response?.status)
        return null;
    } finally {
      setLoading(false);
    }
  };

  return { measurementId, status, loading, error, httpStatus, triggerMeasurement };
};
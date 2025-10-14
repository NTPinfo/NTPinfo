import { useState } from "react";
import axios from "axios";
import { MeasurementRequest } from "../utils/types";


export const useTriggerMeasurement = () => {
  const [measurementId, setMeasurementId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [httpStatus, setHttpStatus] = useState<number>(200);

  const triggerMeasurement = async (server: string, payload: MeasurementRequest) => {
    setLoading(true);
    setError(null);

    try {
      const resp = await axios.post(`${server}/measurements/trigger/`, payload, {
        headers: { "Content-Type": "application/json" },
      });

      const id = resp.data?.id;
      const status = resp.data?.status;

      setMeasurementId(id);
      setStatus(status);
      setHttpStatus(resp.status);

      return id;
    } catch (err: any) {
      console.warn(err);
      setError(err.response?.data?.detail || "Unknown error");
      setHttpStatus(err.response?.status);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { measurementId, status, loading, error, httpStatus, triggerMeasurement };
};
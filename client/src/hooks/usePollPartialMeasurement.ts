import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { PartialMeasurementResult } from "../utils/types";

const SERVER = import.meta.env.VITE_SERVER_HOST_ADDRESS;
export const usePollPartialMeasurement = (measurementId: string | null, interval = 10000) => {

  const [data, setData] = useState<PartialMeasurementResult | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!measurementId) {

      // reset and try again when id is available
      setData(null);
      setStatus(null);
      setError(null);
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }

    const pollPartialResults = async () => {

        setLoading(true);
        abortRef.current = new AbortController();

        try {
            const res = await axios.get(`${SERVER}/measurements/partial-results/${measurementId}`, {
                signal: abortRef.current.signal,
            });

            const partialData: PartialMeasurementResult = res.data;
            setStatus(res.data?.status);
            setData(partialData);

            if (res.data.status === "finished" || res.data.status === "failed") {
                setLoading(false);
                if (intervalRef.current) {
                  clearInterval(intervalRef.current);
                  intervalRef.current = null;
                }
            }
                

        } catch (err: any) {
            setError(err.message);
            setLoading(false);
        }
    }

    intervalRef.current = setInterval(pollPartialResults, interval);
    pollPartialResults();

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (abortRef.current) abortRef.current.abort();
    };
  }, [measurementId, interval])

  return {data, status, loading, error}
}
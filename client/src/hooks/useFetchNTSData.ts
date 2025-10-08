import { useState } from "react";
import { NTSResult } from "../utils/types"
import axios from "axios";

/**
 * Sends a POST request to the backend for receiving Network Time Security (NTS) measurement data.
 * It fetches a single NTS result from the specified endpoint.
 * In the case of an error, it catches the error sent by the backend or Axios.
 * @returns the NTS measurement result as `NTSResult`, or `null`, the loading and error states of the call, and a function to initiate the measurement
 */
export const useFetchNTSData = () => {
  const [data, setData] = useState<NTSResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchNTS = async (payload: { server: string; ipv6_measurement: boolean }) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await axios.post(
        `${import.meta.env.VITE_SERVER_HOST_ADDRESS}/measurements/nts/`,
        payload,
        { headers: { "Content-Type": "application/json" } }
      );
      setData(resp.data ?? null);
      return resp.data ?? null;
    } catch (err: any) {
      setError(err);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, fetchNTS };
};
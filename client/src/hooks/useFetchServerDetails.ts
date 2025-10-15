import { useState } from "react";
import axios from "axios";

const SERVER = import.meta.env.VITE_SERVER_HOST_ADDRESS;

export const useFetchServerDetails = () => {
  const [details, setDetails] = useState<{
    vantage_point_ip: string;
    coordinates: [number, number];
  } | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch vantage point (server) details.
   * Always returns consistent IP + coordinates even on localhost.
   */
  const fetchServerDetails = async (ipType: number = 4) => {
    setLoading(true);
    setError(null);

    try {
      const resp = await axios.get(`${SERVER}/measurements/ntpinfo-server-details/${ipType}`);
      const { vantage_point_ip, vantage_point_location } = resp.data;

      const result = {
        vantage_point_ip,
        coordinates: vantage_point_location.coordinates,
      };

      setDetails(result);
      return result;
    } catch (err: any) {
      console.error("Failed to fetch server details:", err);
      setError(err.message || "Failed to fetch server details");
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { details, loading, error, fetchServerDetails };
};
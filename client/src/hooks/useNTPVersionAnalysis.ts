import { useState, useEffect } from "react";
import axios from "axios";

export const useNTPVersionAnalysis = (measurement_id: number | null) => {
  const [versions, setVersions] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!measurement_id) return;
    const fetchVersions = async () => {
      setLoading(true);
      try {
        const resp = await axios.get(`/measurements/ntp_versions/${measurement_id}`);
        setVersions(resp.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || "Failed to fetch version analysis");
      } finally {
        setLoading(false);
      }
    };
    fetchVersions();
  }, [measurement_id]);

  return { versions, loading, error };
};
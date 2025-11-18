import { useState, useEffect } from "react";
import axios from "axios";

const SERVER = import.meta.env.VITE_SERVER_HOST_ADDRESS;

export interface StatisticsData {
  dn_measurements_count: number;
  ip_measurements_count: number;
  nts_measurements_count: number;
  ntp_versions_analyzed_count: {
    analyzed_ntpv1: number;
    analyzed_ntpv2: number;
    analyzed_ntpv3: number;
    analyzed_ntpv4: number;
    analyzed_ntpv5: number;
    success_rate_ntpv1: number;
    success_rate_ntpv2: number;
    success_rate_ntpv3: number;
    success_rate_ntpv4: number;
    success_rate_ntpv5: number;
  };
  ripe_measurements_count: number;
}

export const useFetchStatistics = () => {
  const [data, setData] = useState<StatisticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatistics = async () => {
    setLoading(true);
    setError(null);

    try {
      const resp = await axios.get(`${SERVER}/statistics/measurements_count`);
      setData(resp.data);
      return resp.data;
    } catch (err: any) {
      console.error("Failed to fetch statistics:", err);
      setError(err.message || "Failed to fetch statistics");
      return null;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatistics();
  }, []);

  return { data, loading, error, refetch: fetchStatistics };
};


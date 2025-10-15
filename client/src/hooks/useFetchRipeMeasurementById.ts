import { useState, useCallback } from 'react';
import axios from 'axios';
import { RIPEData, RipeStatus } from '../utils/types';
import { transformJSONDataToRIPEData } from '../utils/transformJSONDataToRIPEData';

interface RipeMeasurementResult {
  ripeData: RIPEData[] | null;
  status: RipeStatus | null;
  error: string | null;
}

export const useFetchRipeMeasurementById = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRipeMeasurementById = useCallback(async (ripeMeasurementId: string): Promise<RipeMeasurementResult> => {
    if (!ripeMeasurementId) {
      return {
        ripeData: null,
        status: null,
        error: 'No RIPE measurement ID provided'
      };
    }

    setLoading(true);
    setError(null);

    try {
      const serverUrl = `${import.meta.env.VITE_SERVER_HOST_ADDRESS}`;
      const response = await axios.get(`${serverUrl}/measurements/ripe/${ripeMeasurementId}`);
      
      const respData = response.data;
      const result: RipeMeasurementResult = {
        ripeData: null,
        status: null,
        error: null
      };

      // Process RIPE data
      if (respData.results) {
        const transformedData = respData.results.map((d: any) => transformJSONDataToRIPEData(d));
        result.ripeData = transformedData;
      }

      // Set status based on response
      if (respData.status === "complete" || respData.status === "timeout") {
        result.status = "complete";
      } else if (respData.status === "partial_results") {
        result.status = "partial_results";
      } else if (respData.status === "pending") {
        result.status = "pending";
      } else if (respData.status === "error") {
        result.status = "error";
        result.error = respData.message || "Unknown RIPE measurement error";
      }

      return result;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch RIPE measurement results';
      setError(errorMessage);
      return {
        ripeData: null,
        status: "error",
        error: errorMessage
      };
    } finally {
      setLoading(false);
    }
  }, []);

  return { fetchRipeMeasurementById, loading, error };
};

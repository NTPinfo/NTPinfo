import { useState, useCallback } from 'react';
import axios from 'axios';
import { NTPData, NTSResult, NTPVersionsData } from '../utils/types';
import { transformJSONDataToNTPData } from '../utils/transformJSONDataToNTPData';
import { transformFullMeasurementMainToNTPData } from '../utils/transformFullMeasurementMainToNTPData';
import { transformJSONDataToNTPVerData } from '../utils/transformJSONDataToNTPverData';

interface MeasurementResult {
  ntpData: NTPData[] | null;
  ntsData: NTSResult | null;
  versionData: NTPVersionsData | null;
  ripeId: string | null;
  error: string | null;
  status: string | null;
}

export const useFetchMeasurementById = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMeasurementById = useCallback(async (measurementId: string): Promise<MeasurementResult> => {
    if (!measurementId) {
      return {
        ntpData: null,
        ntsData: null,
        versionData: null,
        ripeId: null,
        error: 'No measurement ID provided',
        status: null
      };
    }

    setLoading(true);
    setError(null);

    try {
      const serverUrl = `${import.meta.env.VITE_SERVER_HOST_ADDRESS}`;
      const response = await axios.get(`${serverUrl}/measurements/results/${measurementId}`);
      
      const respData = response.data;
      const result: MeasurementResult = {
        ntpData: null,
        ntsData: null,
        versionData: null,
        ripeId: respData.id_ripe || null,
        error: respData.response_error || null,
        status: respData.status || null
      };

      // Process NTP data
      if (respData.ip_measurements && respData.ip_measurements?.length > 0) {
        const ipMeasurements = respData.ip_measurements;
        const mapped = ipMeasurements
          .map((ip: any) => transformFullMeasurementMainToNTPData(ip.main_measurement) || transformJSONDataToNTPData(ip.main_measurement))
          .filter((x: any): x is NTPData => Boolean(x));
        result.ntpData = mapped.length ? mapped : null;
      } else if (respData.main_measurement) {
        const transformed = transformFullMeasurementMainToNTPData(respData.main_measurement) || transformJSONDataToNTPData(respData.main_measurement);
        result.ntpData = transformed ? [transformed] : null;
      }

      // Process NTS data
      result.ntsData = respData.nts ?? null;

      // Process NTP versions data
      if (respData.id_vs) {
        try {
          const vsResponse = await axios.get(`${serverUrl}/measurements/ntp_versions/${respData.id_vs}`);
          result.versionData = transformJSONDataToNTPVerData(vsResponse.data);
        } catch (err) {
          console.warn("NTP versions fetch failed", err);
        }
      }

      return result;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch measurement results';
      setError(errorMessage);
      return {
        ntpData: null,
        ntsData: null,
        versionData: null,
        ripeId: null,
        error: errorMessage,
        status: null
      };
    } finally {
      setLoading(false);
    }
  }, []);

  return { fetchMeasurementById, loading, error };
};

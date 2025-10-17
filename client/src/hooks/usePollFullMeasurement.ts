import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { transformJSONDataToNTPData } from "../utils/transformJSONDataToNTPData.ts";
import { transformFullMeasurementMainToNTPData } from "../utils/transformFullMeasurementMainToNTPData";
import { transformJSONDataToNTPVerData } from "../utils/transformJSONDataToNTPverData.ts";
import { NTPData } from "../utils/types.ts";
import { useFetchRIPEData } from "./useFetchRipeData.ts";
import { usePollPartialMeasurement } from "./usePollPartialMeasurement.ts";
// interface AggregatedDNMeasurement {
//   status: string;
//   ripeData?: any;
//   nts?: any; // DN-level NTS
//   ipMeasurements?: {
//     search_id: string;
//     status: string;
//     mainMeasurement: NTPData;
//     nts?: any;
//     ntpVersions?: any;
//     responseError?: string | null;
//   }[];
//   responseError?: string | null;
//   mainMeasurement?: NTPData | null;
//   ntpVersions?: any;
// }
const SERVER = import.meta.env.VITE_SERVER_HOST_ADDRESS;
export const usePollFullMeasurement = (measurementId: string | null, interval = 10000
) => {
  const [ntpData, setNtpData] = useState<NTPData[] | null>(null);
  const [ntsData, setNtsData] = useState<any>(null);
  const [ripeId, setRipeId] = useState<string | null>(null);
  const [versionData, setVersionData] = useState<any>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const prevMeasurementId = useRef<string | null>(null);
  const fetchedVersionIdRef = useRef<string | null>(null);

  const [ntpVerLoading, setNtpVerLoading] = useState(false);

  const { result: ripeData, status: ripeStatus, error: ripeError } = useFetchRIPEData(ripeId);
  const { ntpVersionsId } = usePollPartialMeasurement(measurementId);

  useEffect(() => {
    // Start polling as soon as we have a measurement ID. 
    if (!measurementId) {
      return;
    }

    // Only start new polling if this is a different measurement ID
    if (prevMeasurementId.current === measurementId) return;
    prevMeasurementId.current = measurementId;

    // Clean up any existing polling
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    
    const controller = new AbortController();
    
    // Reset all data when starting a new measurement
    setError(null);
    setNtpData(null);
    setNtsData(null);
    setVersionData(null);
    setRipeId(null);
    setStatus(null);
    setNtpVerLoading(true);
    fetchedVersionIdRef.current = null;

    const pollFullMeasurement = async () => {
      try {
            const res = await axios.get(
                `${SERVER}/measurements/results/${measurementId}`,
                 { signal: controller.signal }
            )

            const respData = res.data;
            setStatus(respData.status);

            //RIPE
            if (respData.id_ripe && respData.id_ripe !== ripeId) {
              setRipeId(respData.id_ripe);
            }

            //Main measurement
            if (respData.ip_measurements && respData.ip_measurements?.length > 0) {
                const ipMeasurements = respData.ip_measurements
                const mapped = ipMeasurements
                  .map((ip: any) => transformFullMeasurementMainToNTPData(ip.main_measurement) || transformJSONDataToNTPData(ip.main_measurement))
                  .filter((x: any): x is NTPData => Boolean(x))
                setNtpData(mapped.length ? mapped : null)
                setError(respData.response_error)
            } else if (respData.main_measurement) {
                const transformed = transformFullMeasurementMainToNTPData(respData.main_measurement) || transformJSONDataToNTPData(respData.main_measurement)
                setNtpData(transformed ? [transformed] : null)
                setError(respData.response_error)
            }

            //NTS
            setNtsData(respData.nts ?? null)


            // stop polling if finished or failed
            if (respData.status === "finished" || respData.status === "failed") {
                if (intervalRef.current) {
                  clearInterval(intervalRef.current);
                  intervalRef.current = null;
                }
            }
        } catch (err: any) {
            setError(err?.message || "Polling failed")
            if (intervalRef.current) {
              clearInterval(intervalRef.current)
              intervalRef.current = null
            }
        }
    }

    intervalRef.current = setInterval(pollFullMeasurement, interval);
    pollFullMeasurement();

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
      controller.abort();
    };
  
  }, [measurementId, interval]);

  //Get NTP Versions ID from partial results and poll specific endpoint
  useEffect(() => {
  if (!ntpVersionsId) return;
  if (fetchedVersionIdRef.current === ntpVersionsId) return;

  fetchedVersionIdRef.current = ntpVersionsId;

  const fetchVersions = async () => {
    try {

      const vsRes = await axios.get(`${SERVER}/measurements/ntp_versions/${ntpVersionsId}`);
      setVersionData(transformJSONDataToNTPVerData(vsRes.data));
      setNtpVerLoading(false);
    } catch (err) {
      console.warn("NTP versions fetch failed:", err);
    }
  };

  fetchVersions();
}, [ntpVersionsId]);

  return { ntpData, ntsData, ripeData, versionData, status, error, ripeStatus, ripeError, ripeId, ntpVerLoading};
}
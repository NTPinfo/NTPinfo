import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { transformJSONDataToNTPData } from "../utils/transformJSONDataToNTPData.ts";
import { transformJSONDataToNTPVerData } from "../utils/transformJSONDataToNTPverData.ts";
import { NTPData } from "../utils/types.ts";
import { useFetchRIPEData } from "./useFetchRipeData.ts";
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
export const usePollFullMeasurement = (measurementId: string | null,  partialData: any, interval = 3000
) => {
  const [ntpData, setNtpData] = useState<NTPData | null>(null);
  const [ntsData, setNtsData] = useState<any>(null);
  const [ripeId, setRipeId] = useState<string | null>(null);
  const [versionData, setVersionData] = useState<any>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const prevMeasurementId = useRef<string | null>(null);

  const { result: ripeData, status: ripeStatus, error: ripeError } = useFetchRIPEData(ripeId);

  useEffect(() => {

    if (!measurementId || !partialData) {
      return;
    }

    if (prevMeasurementId.current === measurementId) return;
    prevMeasurementId.current = measurementId;

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    const controller = new AbortController();
    
    setError(null)

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
                const firstIP = respData.ip_measurements[0]
               setNtpData(transformJSONDataToNTPData(firstIP.main_measurement))
               setError(firstIP.response_error)
            } else if (respData.main_measurement) {
                setNtpData(transformJSONDataToNTPData(respData.main_measurement))
                setError(respData.response_error)
            }

            //NTS
            if (respData.nts) setNtsData(respData.nts ?? null)

            //NTP versions
            if (respData.id_vs) {
                try {
                    const vsRes = await axios.get(
                        `${SERVER}/measurements/ntp_versions/${respData.id_vs}`
                    )
                    setVersionData(transformJSONDataToNTPVerData(vsRes.data))
                } catch (err) {
                    console.warn("NTP versions failed", err)
                }
            }

            //Error
            if (respData.response_error) setError(respData.response_error)

        

            // stop polling if finished or failed
            if (respData.status === "finished" || respData.status === "failed") {
                clearInterval(interval)
              
            }
        } catch (err: any) {
            setError(err)
            
            if (intervalRef.current) clearInterval(intervalRef.current)
        }
    }

    intervalRef.current = setInterval(pollFullMeasurement, interval);
    pollFullMeasurement();

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
      controller.abort();
    };
  }, [measurementId, partialData, interval, ripeId]);

  return { ntpData, ntsData, ripeData, versionData, status, error, ripeStatus, ripeError};
}
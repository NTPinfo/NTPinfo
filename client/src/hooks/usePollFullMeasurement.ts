import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { transformJSONDataToNTPData } from "../utils/transformJSONDataToNTPData.ts";
import { transformJSONDataToRIPEData } from "../utils/transformJSONDataToRIPEData.ts";
import { NTPData } from "../utils/types.ts";

interface AggregatedDNMeasurement {
  status: string;
  ripeData?: any;
  nts?: any; // DN-level NTS
  ipMeasurements?: {
    search_id: string;
    status: string;
    mainMeasurement: NTPData;
    nts?: any;
    ntpVersions?: any;
    responseError?: string | null;
  }[];
  responseError?: string | null;
  mainMeasurement?: NTPData | null;
  ntpVersions?: any;
}

export const usePollFullMeasurement = (measurementId: string | null,  interval = 3000
) => {
  const [result, setResult] = useState<AggregatedDNMeasurement| null>(null);

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const prevMeasurementId = useRef<string | null>(null);

  useEffect(() => {
    //astea sunt asa ca era la fel si la ripe

    if (!measurementId) {
      setResult(null);
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
    
    setLoading(true)
    setError(null)

    const pollFullMeasurement = async () => {
      try {
            const res = await axios.get(
                `${import.meta.env.VITE_SERVER_HOST_ADDRESS}/measurements/results/${measurementId}`,
                 { signal: controller.signal }
            )

            const respData = res.data
            const aggregated: AggregatedDNMeasurement = { status: respData.status }

            //RIPE
            if (respData.id_ripe) {
                try {
                    const ripeRes = await axios.get(
                        `${import.meta.env.VITE_SERVER_HOST_ADDRESS}/measurements/ripe/${respData.id_ripe}`
                    )
                    aggregated.ripeData = ripeRes.data?.results?.map(transformJSONDataToRIPEData)
                } catch (err) {
                    console.warn("RIPE fetch failed", err)
                }
            }

            //Main measurement
            if (respData.ip_measurements && respData.ip_measurements.length > 0) {
                const firstIP = respData.ip_measurements[0]
                aggregated.ipMeasurements = respData.ip_measurements || []
                aggregated.responseError = firstIP.response_error
            } else if (respData.main_measurement) {
                aggregated.mainMeasurement = transformJSONDataToNTPData(respData.main_measurement)
                aggregated.responseError = respData.response_error
            }

            //NTS
            if (respData.nts) aggregated.nts = respData.nts

            //NTP versions
            if (respData.id_vs) {
                try {
                    const vsRes = await axios.get(
                        `${import.meta.env.VITE_SERVER_HOST_ADDRESS}/measurements/ntp_versions/${respData.id_vs}`
                    )
                    aggregated.ntpVersions = vsRes.data
                } catch (err) {
                    console.warn("NTP versions f failed", err)
                }
            }

            //Error
            if (respData.response_error) aggregated.responseError = respData.response_error

            setResult(aggregated)

            // stop polling if finished or failed
            if (respData.status === "finished" || respData.status === "failed") {
                if (intervalRef.current) clearInterval(intervalRef.current)
                setLoading(false)
            }
        } catch (err: any) {
            setError(err)
            setLoading(false)
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
  }, [measurementId, interval]);

  return { result, loading, error};
}
import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { transformJSONDataToNTPData } from "../utils/transformJSONDataToNTPData.ts";
import { transformFullMeasurementMainToNTPData } from "../utils/transformFullMeasurementMainToNTPData";
import { transformJSONDataToNTPVerData } from "../utils/transformJSONDataToNTPverData.ts";
import { NTPData } from "../utils/types.ts";
import { useFetchRIPEData } from "./useFetchRipeData.ts";

const SERVER = import.meta.env.VITE_SERVER_HOST_ADDRESS;

export type MeasurementStep = 
  | "pending"
  | "starting RIPE measurement"
  | "adding ntp measurements"
  | "adding nts"
  | "analyzing ntp versions"
  | "finished"
  | "failed";

export const usePollIncrementalMeasurement = (
  measurementId: string | null,
  pollInterval = 3000
) => {
  const [ntpData, setNtpData] = useState<NTPData[] | null>(null);
  const [ntsData, setNtsData] = useState<any>(null);
  const [ripeId, setRipeId] = useState<string | null>(null);
  const [versionData, setVersionData] = useState<any>(null);
  const [status, setStatus] = useState<MeasurementStep | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ntpVerLoading, setNtpVerLoading] = useState(false);

  // Track what we've already fetched to avoid duplicate requests
  const fetchedNtpVersionsIdRef = useRef<number | null>(null);
  const fetchedIpMeasurementsRef = useRef<Set<string>>(new Set());
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const prevMeasurementId = useRef<string | null>(null);
  const isMountedRef = useRef<boolean>(true);

  const { result: ripeData, status: ripeStatus, error: ripeError } = useFetchRIPEData(ripeId);

  // Poll for NTP versions when ID becomes available
  useEffect(() => {
    if (!fetchedNtpVersionsIdRef.current) return;

    const fetchNtpVersions = async () => {
      try {
        setNtpVerLoading(true);
        const vsRes = await axios.get(`${SERVER}/measurements/ntp_versions/${fetchedNtpVersionsIdRef.current}`);
        if (isMountedRef.current) {
          setVersionData(transformJSONDataToNTPVerData(vsRes.data));
          setNtpVerLoading(false);
        }
      } catch (err: any) {
        if (isMountedRef.current) {
          console.warn("NTP versions fetch failed:", err);
          setNtpVerLoading(false);
        }
      }
    };

    fetchNtpVersions();
  }, [fetchedNtpVersionsIdRef.current]);

  // Main polling effect
  useEffect(() => {
    isMountedRef.current = true;
    
    if (!measurementId) {
      // Reset state when no measurement ID
      setNtpData(null);
      setNtsData(null);
      setVersionData(null);
      setRipeId(null);
      setStatus(null);
      setError(null);
      setNtpVerLoading(false);
      fetchedNtpVersionsIdRef.current = null;
      fetchedIpMeasurementsRef.current.clear();
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    // Only reset if this is a different measurement ID
    const isNewMeasurement = prevMeasurementId.current !== measurementId;
    if (isNewMeasurement) {
      prevMeasurementId.current = measurementId;
      
      // Clean up any existing polling
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }

      // Reset state for new measurement
      setNtpData(null);
      setNtsData(null);
      setVersionData(null);
      setRipeId(null);
      setStatus(null);
      setError(null);
      setNtpVerLoading(false);
      fetchedNtpVersionsIdRef.current = null;
      fetchedIpMeasurementsRef.current.clear();
    }

    // Fetch IP measurements separately to avoid abort controller conflicts
    const fetchIpMeasurement = async (ipMeasurementId: string) => {
      try {
        const ipRes = await axios.get(
          `${SERVER}/measurements/partial-results/${ipMeasurementId}`
        );
        
        if (!isMountedRef.current) return;
        
        const ipData = ipRes.data;
        if (ipData.main_measurement) {
          const transformed = transformFullMeasurementMainToNTPData(ipData.main_measurement) ||
                             transformJSONDataToNTPData(ipData.main_measurement);
          
          if (transformed) {
            setNtpData(prev => {
              const existing = prev || [];
              // Avoid duplicates
              const exists = existing.some(
                item => item.ip === transformed.ip && item.measurement_id === transformed.measurement_id
              );
              if (exists) return existing;
              return [...existing, transformed];
            });
          }
        }

        // Check for NTP versions in IP measurement
        if (ipData.ntp_versions_id && 
            fetchedNtpVersionsIdRef.current !== ipData.ntp_versions_id) {
          fetchedNtpVersionsIdRef.current = ipData.ntp_versions_id;
        }
      } catch (err: any) {
        if (err.name !== 'AbortError' && err.name !== 'CanceledError' && isMountedRef.current) {
          console.warn(`Failed to fetch IP measurement ${ipMeasurementId}:`, err);
        }
      }
    };

    const pollPartialResults = async () => {
      try {
        const res = await axios.get(
          `${SERVER}/measurements/partial-results/${measurementId}`
        );

        if (!isMountedRef.current) return;

        const partialData = res.data;
        const currentStatus = partialData.status as MeasurementStep;
        setStatus(currentStatus);

        // Update RIPE ID if available
        if (partialData.id_ripe) {
          setRipeId(prev => {
            if (prev !== partialData.id_ripe) {
              return partialData.id_ripe;
            }
            return prev;
          });
        }

        // Handle main measurement (for IP measurements)
        if (partialData.main_measurement) {
          const transformed = transformFullMeasurementMainToNTPData(partialData.main_measurement) ||
                             transformJSONDataToNTPData(partialData.main_measurement);
          if (transformed) {
            setNtpData(prev => {
              // For IP measurements, replace the array
              if (prev && prev.length > 0 && prev[0].ip === transformed.ip) {
                return prev; // Already have this one
              }
              return [transformed];
            });
          }
        }

        // Handle NTS data (always available in partial results when ready)
        if (partialData.nts) {
          setNtsData(partialData.nts);
        }

        // Handle NTP versions ID
        if (partialData.ntp_versions_id && 
            fetchedNtpVersionsIdRef.current !== partialData.ntp_versions_id) {
          fetchedNtpVersionsIdRef.current = partialData.ntp_versions_id;
        }

        // Handle IP measurements for domain name measurements
        if (partialData.ip_measurements_ids && Array.isArray(partialData.ip_measurements_ids)) {
          for (const ipMeasurementId of partialData.ip_measurements_ids) {
            // Handle both string format ("ip123") and object format ({search_id: "ip123"})
            const idStr = typeof ipMeasurementId === 'string' 
              ? ipMeasurementId 
              : (ipMeasurementId?.search_id || String(ipMeasurementId));
            
            if (idStr && !fetchedIpMeasurementsRef.current.has(idStr)) {
              fetchedIpMeasurementsRef.current.add(idStr);
              // Fetch IP measurement asynchronously without abort controller
              fetchIpMeasurement(idStr);
            }
          }
        }

        // Handle errors
        if (partialData.response_error) {
          setError(partialData.response_error);
        }
        if (partialData.ripe_error) {
          console.warn("RIPE error:", partialData.ripe_error);
        }

        // Stop polling if finished or failed
        if (currentStatus === "finished" || currentStatus === "failed") {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        }
      } catch (err: any) {
        if (!isMountedRef.current) return;
        
        if (err.name === 'AbortError' || err.name === 'CanceledError') {
          // Request was aborted, ignore
          return;
        }
        console.error("Polling failed:", err);
        setError(err?.message || "Polling failed");
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    };

    // Start polling if not already active
    if (!intervalRef.current) {
      intervalRef.current = setInterval(pollPartialResults, pollInterval);
      pollPartialResults(); // Initial poll
    }

    return () => {
      isMountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [measurementId, pollInterval]);

  return {
    ntpData,
    ntsData,
    ripeData,
    versionData,
    status,
    error,
    ripeStatus,
    ripeError,
    ripeId,
    ntpVerLoading,
  };
};

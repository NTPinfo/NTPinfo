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
  const [ripeInitError, setRipeInitError] = useState<string | null>(null);
  const [versionData, setVersionData] = useState<any>(null);
  const [status, setStatus] = useState<MeasurementStep | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ntpVerLoading, setNtpVerLoading] = useState(false);
  const [expectedIpCount, setExpectedIpCount] = useState<number>(0);

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
      setRipeInitError(null);
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
      setRipeInitError(null);
      setStatus(null);
      setError(null);
      setNtpVerLoading(false);
      fetchedNtpVersionsIdRef.current = null;
      fetchedIpMeasurementsRef.current.clear();
    }

    // Helper function to create error entry from failed IP measurement
    const createErrorEntry = (ipMeasurement: any): NTPData => {
      return {
        ntp_version: 0,
        vantage_point_ip: "",
        ip: ipMeasurement.server || "",
        server_name: "",
        is_anycast: false,
        country_code: "",
        coordinates: [0, 0],
        ntp_server_ref_parent_ip: null,
        ref_id: "",
        client_sent_time: -1,
        server_recv_time: -1,
        server_sent_time: -1,
        client_recv_time: -1,
        offset: -1,
        RTT: -1,
        stratum: -1,
        precision: 0,
        root_delay: 0,
        poll: 0,
        root_dispersion: 0,
        ntp_last_sync_time: -1,
        leap: 0,
        jitter: null,
        nr_measurements_jitter: 0,
        asn_ntp_server: "",
        time: Date.now(),
        measurement_id: ipMeasurement.search_id || null,
        hasError: true,
        errorMessage: ipMeasurement.response_error || null,
        response_version: ipMeasurement.response_version || null,
      };
    };

    // Fetch IP measurements separately to avoid abort controller conflicts
    const fetchIpMeasurement = async (ipMeasurementId: string) => {
      try {
        const ipRes = await axios.get(
          `${SERVER}/measurements/partial-results/${ipMeasurementId}`
        );
        
        if (!isMountedRef.current) return;
        
        const ipData = ipRes.data;
        
        // Handle successful measurement
        if (ipData.main_measurement) {
          const transformed = transformFullMeasurementMainToNTPData(ipData.main_measurement) ||
                             transformJSONDataToNTPData(ipData.main_measurement);
          
          if (transformed) {
            // Always set response_version from IP measurement (can be null/undefined)
            transformed.response_version = ipData.response_version;
            
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
        // Handle failed measurement
        else if (ipData.response_error) {
          const errorEntry = createErrorEntry(ipData);
          setNtpData(prev => {
            const existing = prev || [];
            // Avoid duplicates
            const exists = existing.some(
              item => item.measurement_id === errorEntry.measurement_id
            );
            if (exists) return existing;
            return [...existing, errorEntry];
          });
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

    // Fetch full results when measurement is finished to get all IP measurements (including failed ones)
    const fetchFullResultsForDomain = async (dnMeasurementId: string) => {
      try {
        const fullRes = await axios.get(
          `${SERVER}/measurements/results/${dnMeasurementId}`
        );
        
        if (!isMountedRef.current) return;
        
        const fullData = fullRes.data;
        
        // Process all IP measurements (successful and failed)
        if (fullData.ip_measurements && Array.isArray(fullData.ip_measurements)) {
          const allMeasurements: NTPData[] = [];
          
          for (const ipMeasurement of fullData.ip_measurements) {
            if (ipMeasurement.main_measurement) {
              // Successful measurement
              const transformed = transformFullMeasurementMainToNTPData(ipMeasurement.main_measurement) ||
                                 transformJSONDataToNTPData(ipMeasurement.main_measurement);
              if (transformed) {
                // Always set response_version from IP measurement (can be null/undefined)
                transformed.response_version = ipMeasurement.response_version;
                allMeasurements.push(transformed);
              }
            } else if (ipMeasurement.response_error) {
              // Failed measurement
              const errorEntry = createErrorEntry(ipMeasurement);
              allMeasurements.push(errorEntry);
            }
          }
          
          // Update with all measurements, preserving order
          if (allMeasurements.length > 0) {
            setNtpData(allMeasurements);
            setExpectedIpCount(allMeasurements.length);
          }
        }
      } catch (err: any) {
        if (err.name !== 'AbortError' && err.name !== 'CanceledError' && isMountedRef.current) {
          console.warn(`Failed to fetch full results for ${dnMeasurementId}:`, err);
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

        // Update RIPE ID if available, or track error if id_ripe is null
        if (partialData.id_ripe) {
          setRipeId(prev => {
            if (prev !== partialData.id_ripe) {
              return partialData.id_ripe;
            }
            return prev;
          });
          setRipeInitError(null); // Clear error if we got an ID
        } else if (partialData.id_ripe === null && partialData.ripe_error) {
          // Whole RIPE measurement failed
          setRipeInitError(partialData.ripe_error);
          setRipeId(null);
        }

        // Handle main measurement (for IP measurements)
        if (partialData.main_measurement) {
          const transformed = transformFullMeasurementMainToNTPData(partialData.main_measurement) ||
                             transformJSONDataToNTPData(partialData.main_measurement);
          if (transformed) {
            // Add response_version if available
            if (partialData.response_version) {
              transformed.response_version = partialData.response_version;
            }
            
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
          // Track expected IP count for navigation arrows
          const ipIds = partialData.ip_measurements_ids.map((id: any) => 
            typeof id === 'string' ? id : (id?.search_id || String(id))
          ).filter(Boolean);
          setExpectedIpCount(ipIds.length);
          
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
        } else {
          // If no ip_measurements_ids, it's a single IP measurement
          setExpectedIpCount(1);
        }

        // Handle errors
        if (partialData.response_error) {
          setError(partialData.response_error);
        }

        // When finished, fetch full results to get all IP measurements (including failed ones)
        if (currentStatus === "finished" || currentStatus === "failed") {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          
          // Fetch full results for domain name measurements to get all IP measurements
          if (measurementId?.startsWith("dn")) {
            fetchFullResultsForDomain(measurementId);
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
    ripeError: ripeInitError || ripeError, // Prioritize init error (when id_ripe is null) over probe errors - can be string or Error
    ripeId,
    ntpVerLoading,
    expectedIpCount,
  };
};

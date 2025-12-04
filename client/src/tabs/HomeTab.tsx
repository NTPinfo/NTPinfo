import {useEffect, useCallback } from 'react'
import axios from 'axios'
import { HomeCacheState, MeasurementRequest } from '../utils/types' // new import for caching result
import '../styles/HomeTab.css'
import InputSection from '../components/InputSection.tsx'
import ResultSummary from '../components/ResultSummary'
import DownloadButton from '../components/DownloadButton'

import LoadingSpinner from '../components/LoadingSpinner'
import DynamicGraph from '../components/DynamicGraph.tsx'
import { useFetchHistoricalIPData } from '../hooks/useFetchHistoricalIPData.ts'
import { dateFormatConversion } from '../utils/dateFormatConversion.ts'
import {downloadCSV} from '../utils/downloadFormats.ts'
import WorldMap from '../components/WorldMap.tsx'
import Header from '../components/Header.tsx';

import { NTPData } from '../utils/types.ts'

import 'leaflet/dist/leaflet.css'
import ConsentPopup from '../components/ConsentPopup.tsx'
import NTSResultBox from '../components/NTSResultBox.tsx'
import ripeLogo from '../assets/ripe_ncc_white.png'

import { NtpVersionAnalysis } from '../components/NTPVersions.tsx'
import { simplifyErrorMessage } from '../utils/simplifyErrorMessage'

import sidnLogo from '../assets/sidnlabs-log.svg';

import { useTriggerMeasurement } from "../hooks/useTriggerFullMeasurement";
import { usePollIncrementalMeasurement } from "../hooks/usePollIncrementalMeasurement";
import { useFetchServerDetails } from '../hooks/useFetchServerDetails.ts'
import MeasurementStatusIndicator from '../components/MeasurementStatusIndicator.tsx'
import MeasurementSettings from '../components/MeasurementSettings.tsx'
interface HomeTabProps {
  cache: HomeCacheState;
  setCache: React.Dispatch<React.SetStateAction<HomeCacheState>>;
  onVisualizationDataChange: (data: Map<string, NTPData[]> | null) => void;
}

const selectResult = (ntpData: NTPData[] | null): NTPData | null => {
  if(!ntpData) return null

  for(const data of ntpData){
    if(data.stratum !== -1)
      return data
  }
  return ntpData[0]
}

// function HomeTab({ onVisualizationDataChange }: HomeTabProps) {
function HomeTab({ cache, setCache, onVisualizationDataChange }: HomeTabProps) {

  const {
    //
    ntpData,
    ntsResult,
    ripeMeasurementResp,
    versionData,
    //
    chartData,
    measured,
    selMeasurement,
    measurementId, // now used for ResultSummary display
    vantagePointInfo,
    allNtpMeasurements,
    ripeMeasurementStatus,
    ripeMeasurementId,
    ipv6Selected,
    measurementSessionActive,
    measurementSettings,
    currentNtpIndex,
    currentRipeIndex
  } = cache;

  // still local UI state

  // helper to update only the fields we touch
  const updateCache = useCallback(
  (partial: Partial<HomeCacheState>) =>
    setCache(prev => ({ ...prev, ...partial })),
  [setCache]
  );

  const handleIPv6Toggle = (value: boolean) => {
  updateCache({ ipv6Selected: value });
  };


  //Varaibles to log and use API hooks
  
const {fetchData: fetchHistoricalData} = useFetchHistoricalIPData()
  
const {fetchServerDetails} = useFetchServerDetails()
const { triggerMeasurement, loading: triggerLoading, measurementId: fullMeasurementId, httpStatus, error, errorMessage} = useTriggerMeasurement();
const { ntpData: fullNTP, ntsData, ripeData, versionData: fullVersionData, 
      ripeStatus: fetchedRIPEStatus, ripeError: ripeMeasurementError, ripeId: fullRipeId, 
      ntpVerLoading, status: measurementStatus, error: pollingError, expectedIpCount
} = usePollIncrementalMeasurement(fullMeasurementId, 3000);

const ripeTriggerErr = null;
// const ntsLoading = false;
// const ntsError = null;
  // Update cache when loading state changes
  useEffect(() => {
    updateCache({ isLoading: triggerLoading });
  }, [triggerLoading, updateCache]);

  // End measurement session when measurements complete or fail
  useEffect(() => {
    if (measurementSessionActive) {
      // Check if main measurement has finished or failed
      const mainMeasurementDone = measurementStatus === 'finished' || measurementStatus === 'failed';
      
      // Check if RIPE measurements have completed or failed
      const ripeMeasurementDone = ripeMeasurementStatus === 'complete' ||
                                  ripeMeasurementStatus === 'timeout' ||
                                  ripeMeasurementStatus === 'error';
      
      // End session if:
      // 1. Main measurement failed (don't wait for RIPE if main measurement failed)
      // 2. OR main measurement finished AND RIPE is done (or never started)
      if (measurementStatus === 'failed' || 
          (mainMeasurementDone && (ripeMeasurementDone || !ripeMeasurementStatus || ripeMeasurementStatus === null))) {
        updateCache({ measurementSessionActive: false });
      }
    }
  }, [measurementStatus, ripeMeasurementStatus, measurementSessionActive, updateCache]);

  useEffect(() => {
    if (!fetchedRIPEStatus) return;
    updateCache({
      ripeMeasurementResp: ripeData ?? null,
      ripeMeasurementStatus: fetchedRIPEStatus,
    });
  }, [ripeData, fetchedRIPEStatus, updateCache]);

  // Ensure RIPE index stays within bounds when array updates
  useEffect(() => {
    if (!ripeMeasurementResp || ripeMeasurementResp.length === 0) {
      updateCache({ currentRipeIndex: 0 });
      return;
    }
    const safeIndex = Math.max(0, Math.min(currentRipeIndex, ripeMeasurementResp.length - 1));
    if (safeIndex !== currentRipeIndex) {
      updateCache({ currentRipeIndex: safeIndex });
    }
  }, [ripeMeasurementResp, currentRipeIndex, updateCache]);

  // When full NTP data arrives, select a display row and populate cache
  // Update incrementally - don't clear existing measurements when new ones arrive
  useEffect(() => {
    if (!fullNTP || fullNTP.length === 0) {
      // Don't clear allNtpMeasurements if we're still loading - only clear if explicitly reset
      return;
    }
    // Merge new measurements with existing ones, avoiding duplicates
    setCache((prev) => {
      const existing = prev.allNtpMeasurements || [];
      if (existing.length === 0) {
        // First time, just set it
        return {
          ...prev,
          allNtpMeasurements: fullNTP,
          measured: true,
        };
      }
      
      // Merge, avoiding duplicates based on measurement_id or ip+server_name
      const existingIds = new Set(existing.map(m => m.measurement_id || `${m.ip}-${m.server_name}`));
      
      const newMeasurements = fullNTP.filter(m => {
        const id = m.measurement_id || `${m.ip}-${m.server_name}`;
        return !existingIds.has(id);
      });
      
      const merged = [...existing, ...newMeasurements];
      
      return {
        ...prev,
        allNtpMeasurements: merged.length > 0 ? merged : null,
        measured: true,
      };
    });
  }, [fullNTP, setCache]);

  // Update displayed NTP measurement based on current index - show data immediately when available
  useEffect(() => {
    // Priority: Use allNtpMeasurements if available, otherwise use fullNTP directly for immediate display
    const availableMeasurements = allNtpMeasurements && allNtpMeasurements.length > 0 
      ? allNtpMeasurements 
      : (fullNTP && fullNTP.length > 0 ? fullNTP : null);
    
    if (!availableMeasurements || availableMeasurements.length === 0) {
      // Only clear if we're not expecting more (no expectedIpCount or measurement finished)
      if (!expectedIpCount || (measurementStatus === 'finished' || measurementStatus === 'failed')) {
        updateCache({ ntpData: null });
      }
      return;
    }
    
    // If current index is beyond available data but within expected count, keep current index but show last available
    // Otherwise, ensure index is within bounds of actual data
    const maxAvailableIndex = availableMeasurements.length - 1;
    let displayIndex = currentNtpIndex;
    const stillLoading = measurementSessionActive || triggerLoading;
    
    if (currentNtpIndex > maxAvailableIndex) {
      // Index is beyond available data - if we're still loading and within expected count, keep index but show last available
      if (stillLoading && expectedIpCount && currentNtpIndex < expectedIpCount) {
        displayIndex = maxAvailableIndex; // Show last available while waiting
      } else {
        // Out of bounds - clamp to last available
        displayIndex = maxAvailableIndex;
        if (displayIndex !== currentNtpIndex) {
          updateCache({ currentNtpIndex: displayIndex });
        }
      }
    }
    
    const display = availableMeasurements[displayIndex] ?? selectResult(availableMeasurements);
    updateCache({ ntpData: display ?? null });
  }, [allNtpMeasurements, fullNTP, currentNtpIndex, expectedIpCount, measurementStatus, measurementSessionActive, triggerLoading, updateCache]);

  // Sync NTS and NTP Versions when present
  useEffect(() => {
    if (ntsData !== undefined) {
      updateCache({ ntsResult: ntsData ?? null });
    }
  }, [ntsData, updateCache]);

  useEffect(() => {
    if (fullVersionData !== undefined) {
      updateCache({ versionData: fullVersionData ?? null });
    }
  }, [fullVersionData, updateCache]);

  // Store RIPE measurement ID when received
  useEffect(() => {
    if (fullRipeId) {
      updateCache({ ripeMeasurementId: fullRipeId });
    }
  }, [fullRipeId, updateCache]);

  useEffect(() => {
  console.log("📡 measurementId:", fullMeasurementId);
  }, [fullMeasurementId]);

  //just for debugging
  useEffect(() => {
    console.log("NTP:", fullNTP);
    console.log("NTS:", ntsData);
    console.log("RIPE:", ripeData);
    console.log("Versions:", fullVersionData);
  }, [fullNTP, ntsData, ripeData, fullVersionData]);
  //functions for handling state changes
  //

  /**
   * Function called on the press of the search button.
   * Performs a normal measurement call, a historical measurement call for the graph, and a RIPE measurement call for the map.
   * @param query The input given by the user
   */
  const handleInput = async (query: string, useIPv6: boolean) => {
    if (!query.trim())
       return
    if (query.trim().length == 0)
      return

    // Reset ALL cached values for a fresh run and start measurement session
    // Clear all measurement results to avoid showing stale data
    updateCache({
      measurementId: null,
      ripeMeasurementId: null,
      measured: false,
      ntpData: null,
      versionData: null,
      ripeMeasurementResp: null,
      ripeMeasurementStatus: null,
      chartData: null,
      ntsResult: null,
      allNtpMeasurements: null,
      vantagePointInfo: null,
      error: null,
      isLoading: false,
      measurementSessionActive: true,  // Start measurement session
      currentNtpIndex: 0,  // Reset navigation indices
      currentRipeIndex: 0,
    });
    
    // Also clear visualization data for the graph
    onVisualizationDataChange(null);

    /**
     * The payload for the measurement call, containing the server and settings
     */
    const defaultSettings: MeasurementRequest = {
      server: query.trim(),
      ipv6_measurement: useIPv6,
      wanted_ip_type: useIPv6 ? 6 : 4,
      measurement_type: 'ntpv4',
      ntpv5_draft: "draft-ietf-ntp-ntpv5-06",
      analyse_all_ntp_versions: false,
      ntp_versions_to_analyze: ['ntpv3', 'ntpv4', 'ntpv5'],
      ntp_versions_analysis_on_each_ip: false,
      nts_analysis_on_each_ip: false
    };
    
    // Merge with user settings if they exist
    const payload: MeasurementRequest = measurementSettings 
      ? { 
          server: query.trim(), 
          ipv6_measurement: useIPv6, 
          wanted_ip_type: useIPv6 ? 6 : 4,
          measurement_type: measurementSettings.measurement_type || 'ntpv4',
          ntpv5_draft: measurementSettings.ntpv5_draft || "draft-ietf-ntp-ntpv5-06",
          custom_probes_asn: measurementSettings.custom_probes_asn || undefined,
          custom_probes_country: measurementSettings.custom_probes_country || undefined,
          custom_client_ip: measurementSettings.custom_client_ip || undefined,
          // Handle NTP versions settings properly
          // If analyse_all_ntp_versions is true, set it and don't send ntp_versions_to_analyze
          // Otherwise, if ntp_versions_to_analyze has values, send them and set analyse_all_ntp_versions to false
          // If neither is set or both are empty/false, use defaults: analyze v3, v4, v5
          ...(measurementSettings.analyse_all_ntp_versions === true
            ? { analyse_all_ntp_versions: true }
            : (measurementSettings.ntp_versions_to_analyze && Array.isArray(measurementSettings.ntp_versions_to_analyze) && measurementSettings.ntp_versions_to_analyze.length > 0)
              ? { ntp_versions_to_analyze: measurementSettings.ntp_versions_to_analyze, analyse_all_ntp_versions: false }
              : { ntp_versions_to_analyze: ['ntpv3', 'ntpv4', 'ntpv5'], analyse_all_ntp_versions: false }),
          // Hidden options - always set to false
          ntp_versions_analysis_on_each_ip: false,
          nts_analysis_on_each_ip: false
        }
      : defaultSettings;

    /**
     * Get the response from the measurement data endpoint
     */
    //const fullurlMeasurementData = `${import.meta.env.VITE_SERVER_HOST_ADDRESS}/measurements/`
    const serverUrl = `${import.meta.env.VITE_SERVER_HOST_ADDRESS}`
    
    
    try {
      const serverDetails = await fetchServerDetails(payload.wanted_ip_type);
      if (!serverDetails) {
        updateCache({
          measurementSessionActive: false,
          ripeMeasurementStatus: "error",
        });
        return;
        }
      
        updateCache({
          vantagePointInfo:[serverDetails.coordinates, serverDetails.vantage_point_ip],
          measurementSessionActive: true,
           ripeMeasurementStatus: "pending",
        });

      const measurementId  = await triggerMeasurement(serverUrl, payload);
  
      // If triggering failed, end the session and clear all data
      if (!measurementId) {
        updateCache({
          measured: false,
          measurementId: null,
          ripeMeasurementId: null,
          ntpData: null,
          ntsResult: null,
          versionData: null,
          chartData: null,
          allNtpMeasurements: null,
          ripeMeasurementResp: null,
          ripeMeasurementStatus: null,
          vantagePointInfo: null,
          measurementSessionActive: false,
          error: error || null,
        });
        // Also clear visualization data
        onVisualizationDataChange(null);
        return;
      } 

      updateCache({
        measurementId,
        measurementSessionActive: true,
        ripeMeasurementStatus: "pending",
      });

      //HISTORICAL DATA
      /**
      * Get data from past day from historical data endpoint to chart in the graph.
      */
      const startDate = dateFormatConversion(Date.now()-86400000)
      const endDate = dateFormatConversion(Date.now())
      const fullurlHistoricalData = `${import.meta.env.VITE_SERVER_HOST_ADDRESS}/measurements/history/?server=${query}&start=${startDate}&end=${endDate}`
      
      const apiHistoricalResp = await fetchHistoricalData(fullurlHistoricalData);
      const chartData = new Map<string, NTPData[]>();
      chartData.set(payload.server, apiHistoricalResp);
      onVisualizationDataChange(chartData);
      // Only update chart data - don't set ntpData/allNtpMeasurements here
      // The polling hook will update ntpData when new measurements arrive
      updateCache({
        chartData,
        // Keep everything else cleared/reset until new measurement data arrives
      });

       
    } catch {
      // Error handling is done by the triggerMeasurement hook
    }
    
    // RIPE trigger is handled via the new polling flow
  }

  /**
   * Function to determine what value of Measreuemnt to use on the y axis of the visualization graph
   */
  // const handleMeasurementChange = (event: React.ChangeEvent<HTMLInputElement>) => {
  //   setSelMeasurement(event.target.value as Measurement);
  // }
  // const handleMeasurementChange = (e: React.ChangeEvent<HTMLInputElement>) =>
  //   updateCache({ selMeasurement: e.target.value as Measurement })

  return (
    <div className="home-tab-outer">
    <ConsentPopup/>
    <Header />
    {/* The main container for the app, containing the input section, results and graph, and the map */}
    <div className="app-container">
      <div className="input-wrapper">
        <InputSection
          onClick={handleInput}
          loading={triggerLoading || (!fullNTP && measurementSessionActive)}
          ipv6Selected={ipv6Selected}
          onIPv6Toggle={handleIPv6Toggle}
          ripeMeasurementStatus={ripeMeasurementStatus}
          measurementSessionActive={measurementSessionActive}
        />
        <MeasurementSettings
          settings={measurementSettings || {
            server: '',
            ipv6_measurement: ipv6Selected,
            wanted_ip_type: ipv6Selected ? 6 : 4,
            measurement_type: 'ntpv4',
            ntpv5_draft: "draft-ietf-ntp-ntpv5-06",
            analyse_all_ntp_versions: false,
            ntp_versions_to_analyze: ['ntpv3', 'ntpv4', 'ntpv5']
          }}
          onSettingsChange={(newSettings) => updateCache({ measurementSettings: newSettings })}
          disabled={measurementSessionActive || triggerLoading}
        />
      </div>
      {/* Status indicator showing current measurement step */}
      {(measurementSessionActive || measurementStatus) && (
        <MeasurementStatusIndicator 
          status={measurementStatus} 
          isLoading={measurementSessionActive && measurementStatus !== "finished" && measurementStatus !== "failed"}
        />
      )}
      {/* <h3 id="disclaimer">DISCLAIMER: Your IP may be used to get a RIPE probe close to you for the most accurate data. Your IP will not be stored.</h3> */}
        {/* <div className="result-text">
          {((triggerLoading || measurementSessionActive) && measured && (<p>Results</p>)) ||
                    (apiDataLoading && <div className="loading-div">
                        <p>Loading...</p>
                        <LoadingSpinner size="small"/>
                    </div>
                        )}
        </div> */}
      {/* Check if this is any server error (400, 404, 422, 500, 503, etc.) - show only error message, no sections */}
      {(httpStatus >= 400 && errorMessage && !fullMeasurementId && !measurementId && !fullNTP && !allNtpMeasurements && !triggerLoading && !measurementSessionActive) ? (
        <div className="error-only-message" style={{
          backgroundColor: '#fee',
          border: '2px solid #f88',
          borderRadius: '8px',
          padding: '24px',
          margin: '20px 0 20px 40px',
          color: '#c33',
          textAlign: 'left',
          maxWidth: '600px',
          width: 'fit-content'
        }}>
          <h2 style={{ margin: '0 0 12px 0', fontSize: '20px' }}>⚠️ Error {httpStatus || 'Unknown'}</h2>
          <p style={{ margin: 0, fontSize: '16px' }}>
            {simplifyErrorMessage(errorMessage) || errorMessage || 'An error occurred while processing the measurement.'}
          </p>
        </div>
      ) : ((fullNTP && fullNTP.length > 0) || (allNtpMeasurements && allNtpMeasurements.length > 0) || ripeData || pollingError || error || errorMessage || fullMeasurementId || measurementId || measured || measurementStatus === 'failed' || (expectedIpCount && expectedIpCount > 0)) ? (
        <div className="results-and-graph">
          <ResultSummary 
            data={ntpData}
            ripeData={ripeMeasurementResp && ripeMeasurementResp.length > 0 ? ripeMeasurementResp[currentRipeIndex] : null}
            ripeErr={ripeTriggerErr ?? ripeMeasurementError}
            err={error || (pollingError ? new Error(pollingError) : null)}
            errMessage={errorMessage || pollingError || null}
            httpStatus={httpStatus}
            ripeStatus={ripeTriggerErr ? "error" : ripeMeasurementStatus}
            measurementId={measurementId || fullMeasurementId || null}
            allNtpMeasurements={allNtpMeasurements}
            allRipeMeasurements={ripeMeasurementResp}
            currentNtpIndex={currentNtpIndex}
            currentRipeIndex={currentRipeIndex}
            onNtpIndexChange={(index) => updateCache({ currentNtpIndex: index })}
            onRipeIndexChange={(index) => updateCache({ currentRipeIndex: index })}
            expectedIpCount={expectedIpCount}
            isLoading={measurementSessionActive || triggerLoading}
          />

          {/* Div for the visualization graph, and the radios for setting the what measurement to show */}
          {!error && ntpData && chartData && (
            <div className="graphs">
              <div className='graph-box'>
                <DynamicGraph
                  servers={chartData ? Array.from(chartData.keys()) : []}
                  selectedMeasurement={selMeasurement}
                  onMeasurementChange={(measurement) => updateCache({ selMeasurement: measurement })}
                  legendDisplay={false}
                  showTimeInput={false}
                  existingData={chartData}
                />
              </div>
            </div>
          )}
        </div>
      ) : ((triggerLoading || measurementSessionActive) && !fullNTP && !ripeData && !error && !pollingError && !errorMessage && !fullMeasurementId && !measurementId) ? (
        <div className="main-details-loading">
          <div className="loading-div">
            <p>Initializing measurement...</p>
            <LoadingSpinner size="medium"/>
          </div>
        </div>
      ) : null}

      {/* NTS Results Box - shown when measurement has been attempted (hide if error) */}
      {!((httpStatus >= 400) && errorMessage) && (fullNTP || measured || measurementSessionActive || ntsResult || ntsData || measurementId) && (
        <NTSResultBox 
          ntsResult={ntsResult || ntsData || null} 
          loading={!ntsResult && !ntsData && measurementSessionActive} 
          error={null} 
        />
      )}

      {/*Buttons to download results in JSON and CSV format as well as open a popup displaying historical data (hide if error) */}
      {!((httpStatus >= 400) && errorMessage) && fullNTP && (<div className="download-buttons">
        <DownloadButton 
          name="Download JSON" 
          onclick={async () => {
            try {
              const serverUrl = `${import.meta.env.VITE_SERVER_HOST_ADDRESS}`;
              const bundle: any = {
                download_timestamp: new Date().toISOString(),
                measurement_id: measurementId || null,
                ripe_measurement_id: ripeMeasurementId || null
              };
              
              // Fetch raw NTP measurement data from server
              if (measurementId) {
                try {
                  console.log(`Fetching NTP measurement: ${measurementId}`);
                  const ntpResponse = await axios.get(`${serverUrl}/measurements/results/${measurementId}`);
                  bundle.ntp_measurement = ntpResponse.data;
                  console.log('NTP measurement fetched successfully');
                } catch (ntpError: any) {
                  console.error('Failed to fetch NTP measurement:', ntpError);
                  bundle.ntp_measurement_error = {
                    message: ntpError.response?.data?.detail || ntpError.message || 'Error occurred',
                    status: ntpError.response?.status,
                    statusText: ntpError.response?.statusText
                  };
                }
              } else {
                bundle.ntp_measurement_error = 'No measurement ID available';
              }
              
              // Fetch raw RIPE measurement data from server
              if (ripeMeasurementId) {
                try {
                  // Convert to string in case it's a number
                  const ripeIdStr = String(ripeMeasurementId);
                  console.log(`Fetching RIPE measurement: ${ripeIdStr}`);
                  const ripeResponse = await axios.get(`${serverUrl}/measurements/ripe/${ripeIdStr}`);
                  bundle.ripe_measurement = ripeResponse.data;
                  console.log('RIPE measurement fetched successfully');
                } catch (ripeError: any) {
                  console.error('Failed to fetch RIPE measurement:', ripeError);
                  bundle.ripe_measurement_error = {
                    message: ripeError.response?.data?.detail || ripeError.message || 'Error occurred',
                    status: ripeError.response?.status,
                    statusText: ripeError.response?.statusText
                  };
                }
              } else {
                bundle.ripe_measurement_error = 'No RIPE measurement ID available';
              }
              
              // Always download the bundle, even if there are errors (so user can see what went wrong)
              // Download raw JSON object directly (not using downloadJSON which expects an array)
              const json = JSON.stringify(bundle, null, 2);
              const blob = new Blob([json], {type: 'application/json'});
              const downloadLink = document.createElement('a');
              downloadLink.href = window.URL.createObjectURL(blob);
              downloadLink.download = `measurement_data_${measurementId || 'unknown'}_${new Date().toISOString().split('T')[0]}.json`;
              downloadLink.click();
              window.URL.revokeObjectURL(downloadLink.href);
            } catch (error: any) {
              console.error('Failed to download raw JSON:', error);
              const errorMsg = error.response?.data?.detail || error.message || 'Error occurred';
              alert(`Failed to download raw JSON data: ${errorMsg}\n\nCheck the browser console (F12) for more details.`);
            }
          }} 
        />
        <DownloadButton 
          name="Download CSV" 
          onclick={() => {
            const ntpDataArray = allNtpMeasurements ? (Array.isArray(allNtpMeasurements) ? allNtpMeasurements : [allNtpMeasurements]) : [];
            const ripeDataArray = ripeMeasurementResp ? (Array.isArray(ripeMeasurementResp) ? ripeMeasurementResp : [ripeMeasurementResp]) : [];
            downloadCSV([...ntpDataArray, ...ripeDataArray]);
          }} 
        />
      </div>)}
       {!((httpStatus >= 400) && errorMessage) && (fullNTP || ntpData || measured || measurementSessionActive || versionData || fullVersionData || measurementId) && ntpVerLoading && <div className="loading-div">
                        <p>Loading NTP Versions Analysis...</p>
                        <LoadingSpinner size="small"/>
                    </div>
      }
      {!((httpStatus >= 400) && errorMessage) && (fullNTP || ntpData || measured || measurementSessionActive || versionData || fullVersionData || measurementId) && (versionData || fullVersionData || !ntpVerLoading) && (<NtpVersionAnalysis data={versionData || fullVersionData || null}/>)} 
      {/*Map compoment that shows the NTP servers, the vantage point, and the RIPE probes*/}
       {(ripeMeasurementStatus === "complete" || ripeMeasurementStatus === "partial_results" || ripeMeasurementStatus === "timeout") && (
        <div className='map-box'>
          <WorldMap
            probes={ripeMeasurementResp}
            ntpServers={allNtpMeasurements}
            vantagePointInfo={vantagePointInfo}
            status={ripeMeasurementStatus}
          />
        </div>
        )}
    </div>
    <footer className="home-footer">
  <div className="footer-content">
    {/* Hosted by SIDN Labs (logo only) */}
    <div className="hosted-by-section">
      <span className="footer-label">Hosted by</span>
      <a
        href="https://sidnlabs.nl"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="SIDN Labs"
      >
        <img src={sidnLogo} alt="SIDN Labs" className="footer-logo" />
      </a>
    </div>

    {/* Powered by TIME.nl (text) and RIPE Atlas (logo) */}
    <div className="powered-by-section">
      <span className="footer-label">Powered by</span>
      <a
        href="https://time.nl"
        target="_blank"
        rel="noopener noreferrer"
        className="footer-text-link"
      >
        TIME.nl
      </a>

      <span className="footer-and">and</span>

      <a
        href="https://atlas.ripe.net"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="RIPE Atlas"
      >
        <img src={ripeLogo} alt="RIPE Atlas" className="footer-logo-ripe" />
      </a>
    </div>
  </div>
</footer>
    </div>
    );
}

export default HomeTab;
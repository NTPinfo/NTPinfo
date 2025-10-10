import {useEffect, useCallback } from 'react'
import { HomeCacheState } from '../utils/types' // new import for caching result
import '../styles/HomeTab.css'
import InputSection from '../components/InputSection.tsx'
import ResultSummary from '../components/ResultSummary'
import DownloadButton from '../components/DownloadButton'

import LoadingSpinner from '../components/LoadingSpinner'
import DynamicGraph from '../components/DynamicGraph.tsx'
import { useFetchIPData } from '../hooks/useFetchIPData.ts'
import { useFetchHistoricalIPData } from '../hooks/useFetchHistoricalIPData.ts'
import { useFetchRIPEData } from '../hooks/useFetchRipeData.ts'
import { dateFormatConversion } from '../utils/dateFormatConversion.ts'
import {downloadJSON, downloadCSV} from '../utils/downloadFormats.ts'
import WorldMap from '../components/WorldMap.tsx'
import Header from '../components/Header.tsx';

import { NTPData} from '../utils/types.ts'

import 'leaflet/dist/leaflet.css'
import { useTriggerRipeMeasurement } from '../hooks/useTriggerRipeMeasurement.ts'
import { useFetchNTSData } from '../hooks/useFetchNTSData.ts'
import ConsentPopup from '../components/ConsentPopup.tsx'
import NTSResultBox from '../components/NTSResultBox.tsx'
import ripeLogo from '../assets/ripe_ncc_white.png'
import { NtpVersionAnalysis } from '../components/NTPVersions.tsx'

// interface HomeTabProps {
//     onVisualizationDataChange: (data: Map<string, NTPData[]> | null) => void;
// }
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
    ntpData,
    chartData,
    measured,
    selMeasurement,
    measurementId,
    vantagePointInfo,
    allNtpMeasurements,
    ripeMeasurementResp,
    ripeMeasurementStatus,
    ipv6Selected,
    measurementSessionActive,
    ntsResult
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
  //
  // states we need to define
  //
  // const [ntpData, setNtpData] = useState<NTPData | null>(null)
  // const [chartData, setChartData] = useState<Map<string, NTPData[]> | null>(null)
  // const [measured, setMeasured] = useState(false)
  // const [popupOpen, setPopupOpen] = useState(false)
  // const [selOption, setOption] = useState("Last Hour")
  // const [selMeasurement, setSelMeasurement] = useState<Measurement>("offset")
  // const [measurementId, setMeasurementId] = useState<string | null>(null)
  // const [vantagePointIp, setVantagePointIp] = useState<string | null>(null)
  // const [allNtpMeasurements, setAllNtpMeasurements] = useState<NTPData[] | null>(null)

  //Varaibles to log and use API hooks
  const {fetchData: fetchMeasurementData, loading: apiDataLoading, error: apiErrorLoading, httpStatus: respStatus, errorMessage: apiErrDetail} = useFetchIPData()
  const {fetchData: fetchHistoricalData} = useFetchHistoricalIPData()
  const {triggerMeasurement, error: ripeTriggerErr} = useTriggerRipeMeasurement()
  const { fetchNTS, loading: ntsLoading, error: ntsError } = useFetchNTSData()
  const {
    result: fetchedRIPEData,
    status: fetchedRIPEStatus,
    error: ripeMeasurementError
  } = useFetchRIPEData(measurementId)

  // Update cache when loading state changes
  useEffect(() => {
    updateCache({ isLoading: apiDataLoading });
  }, [apiDataLoading, updateCache]);

  // End measurement session when RIPE measurements complete or fail
  useEffect(() => {
    if (measurementSessionActive && ripeMeasurementStatus) {
      if (ripeMeasurementStatus === 'complete' ||
          ripeMeasurementStatus === 'timeout' ||
          ripeMeasurementStatus === 'error') {
        updateCache({ measurementSessionActive: false });
      }
    }
  }, [ripeMeasurementStatus, measurementSessionActive, updateCache]);

  useEffect(() => {
    if (!ripeMeasurementStatus || ripeMeasurementStatus === "complete") return;
    updateCache({
      ripeMeasurementResp: fetchedRIPEData,
      ripeMeasurementStatus: fetchedRIPEStatus,
    });
  }, [ripeMeasurementResp, ripeMeasurementStatus, updateCache, fetchedRIPEData, fetchedRIPEStatus]);

  //
  //functions for handling state changes
  //

  /**
   * Function called on the press of the search button.
   * Performs a normal measurement call, a historical measurement call for the graph, and a RIPE measurement call for the map.
   * @param query The input given by the user
   */
  const handleInput = async (query: string, useIPv6: boolean) => {
    if (query.length == 0)
      return

    //Reset the hook
    // setMeasurementId(null)
    // setMeasured(false)
    // setNtpData(null)
    // setChartData(null)

    // Reset cached values for a fresh run and start measurement session
    updateCache({
      measurementId: null,
      measured: false,
      ntpData: null,
      ripeMeasurementResp: null,
      ripeMeasurementStatus: null,
      chartData: null,
      ntsResult: null,
      measurementSessionActive: true  // Start measurement session
    })

    /**
     * The payload for the measurement call, containing the server and the choice of using IPv6 or not
     */
    const payload = {
      server: query.trim(),
      ipv6_measurement: useIPv6

    }

    /**
     * Get the response from the measurement data endpoint
     */
    const fullurlMeasurementData = `${import.meta.env.VITE_SERVER_HOST_ADDRESS}/measurements/`

    /**
     * Get data from past day from historical data endpoint to chart in the graph.
     */
    const startDate = dateFormatConversion(Date.now()-86400000)
    const endDate = dateFormatConversion(Date.now())
    const fullurlHistoricalData = `${import.meta.env.VITE_SERVER_HOST_ADDRESS}/measurements/history/?server=${query}&start=${startDate}&end=${endDate}`

    const ripePayload = {
      server: query.trim(),
      ipv6_measurement: useIPv6
    }

    // Run all four calls concurrently for better performance
    const [apiMeasurementResp, apiHistoricalResp, ripeTriggerResp, ntsResp] = await Promise.all([
      fetchMeasurementData(fullurlMeasurementData, payload),
      fetchHistoricalData(fullurlHistoricalData),
      triggerMeasurement(ripePayload),
      fetchNTS(payload),
    ])

    // If main measurement failed, end the session
    if (!apiMeasurementResp) {
      updateCache({
        measured: true,
        ntpData: null,
        chartData: null,
        allNtpMeasurements: null,
        ripeMeasurementResp: null,
        ripeMeasurementStatus: 'error',
        measurementSessionActive: false  // End session
      })
      return
    }

    /**
     * Update the stored data and show it again
     */
    const data = selectResult(apiMeasurementResp)
    const chartData = new Map<string, NTPData[]>()
    chartData.set(payload.server, apiHistoricalResp)
    onVisualizationDataChange(chartData)
    updateCache({
      measured: true,
      ntpData: data ?? null,
      chartData,
      allNtpMeasurements: apiMeasurementResp ?? null,
      ripeMeasurementResp: null,          // clear old map
      ripeMeasurementStatus: undefined,        //  "     "
      ntsResult: ntsResp ?? null,         // Store NTS result
      measurementSessionActive: true      // Keep session active for RIPE measurements
    })
    // setVantagePointIp(ripeTriggerResp === null ? null : ripeTriggerResp.parsedData.vantage_point_ip)
    // setMeasurementId(ripeTriggerResp === null ? null : ripeTriggerResp.parsedData.measurementId)

    if (ripeTriggerResp === null) {
      // If RIPE measurement trigger failed, end the session
      updateCache({
        vantagePointInfo: null,
        measurementId: null,
        ripeMeasurementResp: null,
        ripeMeasurementStatus: 'error',
        measurementSessionActive: false  // End session
      })
    } else {
      updateCache({
        //vantagePointInfo: ripeTriggerResp?.parsedData.coordinates && ripeTriggerResp?.parsedData.vantage_point_ip ? [ripeTriggerResp.parsedData.coordinates, ripeTriggerResp.parsedData.vantage_point_ip] : null,
        vantagePointInfo: [ripeTriggerResp?.parsedData.coordinates, ripeTriggerResp?.parsedData.vantage_point_ip],
        measurementId: ripeTriggerResp?.parsedData.measurementId ?? null,
        ripeMeasurementResp: null,          // will be filled by hook
        ripeMeasurementStatus: 'pending',
        measurementSessionActive: true      // Keep session active
      })
    }
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
          loading={apiDataLoading}
          ipv6Selected={ipv6Selected}
          onIPv6Toggle={handleIPv6Toggle}
          ripeMeasurementStatus={ripeMeasurementStatus}
          measurementSessionActive={measurementSessionActive}
        />
      </div>
      {/* <h3 id="disclaimer">DISCLAIMER: Your IP may be used to get a RIPE probe close to you for the most accurate data. Your IP will not be stored.</h3> */}
        <div className="result-text">
          {(!apiDataLoading && measured && (<p>Results</p>)) ||
                    (apiDataLoading && <div className="loading-div">
                        <p>Loading...</p>
                        <LoadingSpinner size="small"/>
                    </div>
                        )}
        </div>
        {/* The main page shown after the main measurement is done */}
      {(ntpData && !apiDataLoading && (<div className="results-and-graph">
        <ResultSummary data={ntpData}
                       ripeData={ripeMeasurementResp?ripeMeasurementResp[0]:null}
                       err={apiErrorLoading}
                       errMessage={apiErrDetail}
                       httpStatus={respStatus}
                       ripeErr={ripeTriggerErr ?? ripeMeasurementError}
                       ripeStatus={ripeTriggerErr ? "error" : ripeMeasurementStatus}/>

        {/* Div for the visualization graph, and the radios for setting the what measurement to show */}
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
      </div>)) || (!ntpData && !apiDataLoading && measured &&
      <ResultSummary data={ntpData} err={apiErrorLoading} httpStatus={respStatus} errMessage={apiErrDetail}
      ripeData={ripeMeasurementResp?ripeMeasurementResp[0]:null} ripeErr={ripeTriggerErr ?? ripeMeasurementError} ripeStatus={ripeTriggerErr ? "error" :  ripeMeasurementStatus}/>)}

      {/* NTS Results Box - shown when NTP data is available */}
      {ntpData && !apiDataLoading && (
        <NTSResultBox 
          ntsResult={ntsResult} 
          loading={ntsLoading} 
          error={ntsError} 
        />
      )}

      {/*Buttons to download results in JSON and CSV format as well as open a popup displaying historical data*/}
      {/*The open popup button is commented out, because it is implemented as a separate tab*/}
      {ntpData && !apiDataLoading && (<div className="download-buttons">
        <DownloadButton 
          name="Download JSON" 
          onclick={() => {
            const bundle: any[] = [ntpData];
            if (ripeMeasurementResp) bundle.push(ripeMeasurementResp[0]);
            if (ntsResult) {
              // Create a wrapper object for NTS data to match the expected format
              const ntsWrapper = { type: 'NTS Data', ...ntsResult };
              bundle.push(ntsWrapper as any);
            }
            downloadJSON(bundle);
          }} 
        />
        <DownloadButton 
          name="Download CSV" 
          onclick={() => downloadCSV(ripeMeasurementResp ? [ntpData, ripeMeasurementResp[0]] : [ntpData])} 
        />
        {ntsResult && (
          <DownloadButton 
            name="Download NTS Result" 
            onclick={() => {
              const ntsWrapper = { type: 'NTS Data', ...ntsResult };
              downloadJSON([ntsWrapper as any]);
            }} 
          />
        )}
      </div>)}

      {ntpData && (<NtpVersionAnalysis measurement_id={2}/>)} 
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
        <span className="powered-by">Powered by</span>
        <a href="https://ripe.net" target="_blank" rel="noopener noreferrer" aria-label="RIPE NCC">
          <img src={ripeLogo} alt="RIPE NCC" className="ripe-logo" />
        </a>
      </div>
    </footer>
    </div>
    );
}

export default HomeTab;
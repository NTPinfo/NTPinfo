import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import HomeTab from './tabs/HomeTab';
import CompareTab from './tabs/CompareTab';
import HistoricalDataTab from './tabs/HistoricalDataTab';
import AboutTab from './tabs/AboutTab';
// import { NTPData } from './utils/types';
import { NTPData, HomeCacheState } from './utils/types';
import { useFetchMeasurementById } from './hooks/useFetchMeasurementById';
import { useFetchRipeMeasurementById } from './hooks/useFetchRipeMeasurementById';
import './App.css';

function App() {
  const [selectedTab, setSelectedTab] = useState(1);
  const [visualizationData, setVisualizationData] = useState<Map<string, NTPData[]> | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  /* ------------------   NEW: cache that outlives HomeTab   ------------------ */
  const initialCache: HomeCacheState = {
    ntpData: null,
    ntsResult: null,
    ripeMeasurementResp: null,
    versionData: null,
    chartData: null,
    measured: false,
    selMeasurement: 'offset',
    measurementId: null,
    ripeMeasurementId: null,
    vantagePointInfo: null,
    allNtpMeasurements: null,
    ripeMeasurementStatus: null,
    ipv6Selected: false,
    isLoading: false,
    measurementSessionActive: false,
    error: null
  };
  const [homeCache, setHomeCache] = useState<HomeCacheState>(initialCache);

  // Hooks for fetching measurement results by ID
  const { fetchMeasurementById } = useFetchMeasurementById();
  const { fetchRipeMeasurementById } = useFetchRipeMeasurementById();

  // Check if any measurement is currently running
  const isMeasurementRunning = homeCache.measurementSessionActive;

  // Reload measurement results when switching to home tab
  useEffect(() => {
    const reloadMeasurementResults = async () => {
      if (selectedTab === 1 && homeCache.measured && homeCache.measurementId) {
        try {
          // Fetch main measurement results
          const measurementResult = await fetchMeasurementById(homeCache.measurementId);
          
          // Update cache with fetched results
          setHomeCache(prev => ({
            ...prev,
            ntpData: measurementResult.ntpData ? measurementResult.ntpData[0] : null,
            allNtpMeasurements: measurementResult.ntpData,
            ntsResult: measurementResult.ntsData,
            versionData: measurementResult.versionData,
            error: measurementResult.error
          }));

          // Fetch RIPE measurement results if we have a RIPE measurement ID
          if (homeCache.ripeMeasurementId) {
            const ripeResult = await fetchRipeMeasurementById(homeCache.ripeMeasurementId);
            
            setHomeCache(prev => ({
              ...prev,
              ripeMeasurementResp: ripeResult.ripeData,
              ripeMeasurementStatus: ripeResult.status,
              error: ripeResult.error || prev.error
            }));
          }
        } catch (error) {
          console.error('Failed to reload measurement results:', error);
        }
      }
    };

    reloadMeasurementResults();
  }, [selectedTab, homeCache.measured, homeCache.measurementId, homeCache.ripeMeasurementId, fetchMeasurementById, fetchRipeMeasurementById]);

  return (

    <div className="app-layout">
      <Sidebar
        selectedTab={selectedTab}
        setSelectedTab={setSelectedTab}
        open={sidebarOpen}
        setOpen={setSidebarOpen}
        isMeasurementRunning={isMeasurementRunning}
      />
      <main className={`app-content${!sidebarOpen ? ' with-sidebar-collapsed' : ''}`}>
        {/* {selectedTab === 1 && <HomeTab onVisualizationDataChange={setVisualizationData} />} */}
        {selectedTab === 1 && (
          <HomeTab
            cache={homeCache}
            setCache={setHomeCache}
            onVisualizationDataChange={setVisualizationData}
          />
        )}
        {selectedTab === 2 && <HistoricalDataTab data={visualizationData} />}
        {selectedTab === 3 && <CompareTab />}
        {selectedTab === 4 && <AboutTab />}
      </main>
    </div>
  );
}

export default App

import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import HomeTab from './tabs/HomeTab';
import CompareTab from './tabs/CompareTab';
import HistoricalDataTab from './tabs/HistoricalDataTab';
import SearchTab from './tabs/SearchTab';
import AboutTab from './tabs/AboutTab';
// import { NTPData } from './utils/types';
import { NTPData, HomeCacheState } from './utils/types';
import { useFetchMeasurementById } from './hooks/useFetchMeasurementById';
import { useFetchRipeMeasurementById } from './hooks/useFetchRipeMeasurementById';
import './App.css';

function App() {
  const [selectedTab, setSelectedTab] = useState(1);
  const [previousTab, setPreviousTab] = useState(1);
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
    error: null,
    measurementSettings: null,
    currentNtpIndex: 0,
    currentRipeIndex: 0
  };
  const [homeCache, setHomeCache] = useState<HomeCacheState>(initialCache);

  // Hooks for fetching measurement results by ID
  const { fetchMeasurementById } = useFetchMeasurementById();
  const { fetchRipeMeasurementById } = useFetchRipeMeasurementById();

  // Check if any measurement is currently running
  const isMeasurementRunning = homeCache.measurementSessionActive;

  // Track previous tab and reset cache when returning to HomeTab from another tab
  useEffect(() => {
    if (selectedTab !== previousTab) {
      // Tab changed
      if (selectedTab === 1 && previousTab !== 1 && !homeCache.measurementSessionActive) {
        // Coming back to HomeTab from another tab, and no measurement is running
        // Reset the cache to initial state for a clean page
        setHomeCache(initialCache);
      }
      setPreviousTab(selectedTab);
    }
  }, [selectedTab, previousTab, homeCache.measurementSessionActive]);

  // Reload measurement results when switching to home tab (only if measurement is still active)
  useEffect(() => {
    const reloadMeasurementResults = async () => {
      if (selectedTab === 1 && homeCache.measured && homeCache.measurementId && homeCache.measurementSessionActive) {
        try {
          // Fetch main measurement results
          const measurementResult = await fetchMeasurementById(homeCache.measurementId);
          
          // Update cache with fetched results
          setHomeCache(prev => {
            const allNtp = measurementResult.ntpData;
            const currentIndex = prev.currentNtpIndex || 0;
            const safeIndex = allNtp && allNtp.length > 0 
              ? Math.max(0, Math.min(currentIndex, allNtp.length - 1))
              : 0;
            return {
              ...prev,
              ntpData: allNtp && allNtp.length > 0 ? allNtp[safeIndex] : null,
              allNtpMeasurements: allNtp,
              currentNtpIndex: safeIndex,
              ntsResult: measurementResult.ntsData,
              versionData: measurementResult.versionData,
              error: measurementResult.error
            };
          });

          // Fetch RIPE measurement results if we have a RIPE measurement ID
          if (homeCache.ripeMeasurementId) {
            const ripeResult = await fetchRipeMeasurementById(homeCache.ripeMeasurementId);
            
            setHomeCache(prev => {
              const allRipe = ripeResult.ripeData;
              const currentIndex = prev.currentRipeIndex || 0;
              const safeIndex = allRipe && allRipe.length > 0
                ? Math.max(0, Math.min(currentIndex, allRipe.length - 1))
                : 0;
              return {
                ...prev,
                ripeMeasurementResp: allRipe,
                currentRipeIndex: safeIndex,
                ripeMeasurementStatus: ripeResult.status,
                error: ripeResult.error || prev.error
              };
            });
          }
        } catch (error) {
          console.error('Failed to reload measurement results:', error);
        }
      }
    };

    reloadMeasurementResults();
  }, [selectedTab, homeCache.measured, homeCache.measurementId, homeCache.ripeMeasurementId, homeCache.measurementSessionActive, fetchMeasurementById, fetchRipeMeasurementById]);

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
        {/* SearchTab temporarily hidden - will be updated in future */}
        {/* {selectedTab === 4 && <SearchTab />} */}
        {selectedTab === 5 && <AboutTab />}
      </main>
    </div>
  );
}

export default App

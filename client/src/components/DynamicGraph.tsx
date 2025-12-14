import React, { useState, useEffect } from 'react';
import { NTPData } from '../utils/types.ts';
import LineChart from './LineGraph.tsx';
import { Measurement } from '../utils/types.ts';
import { TimeInput } from './TimeInput.tsx';
import { useFetchHistoricalIPData } from '../hooks/useFetchHistoricalIPData.ts';
import { dateFormatConversion } from '../utils/dateFormatConversion.ts';
import LoadingSpinner from './LoadingSpinner.tsx';
import '../styles/DynamicGraph.css';

interface DynamicGraphProps {
  servers: string[];
  selectedMeasurement: Measurement;
  onMeasurementChange: (measurement: Measurement) => void;
  legendDisplay?: boolean;
  showTimeInput?: boolean;
  existingData?: Map<string, NTPData[]> | null;
  onDataChange?: (data: Map<string, NTPData[]> | null) => void;
}

export default function DynamicGraph({
  servers,
  selectedMeasurement,
  onMeasurementChange,
  legendDisplay = false,
  showTimeInput = true,
  existingData = null,
  onDataChange
}: DynamicGraphProps) {
  const [selOption, setSelOption] = useState("Last Day");
  const [customFrom, setCustomFrom] = useState<string>("");
  const [customTo, setCustomTo] = useState<string>("");
  const [data, setData] = useState<Map<string, NTPData[]> | null>(existingData);

  const { fetchData: fetchHistoricalData, loading: apiHistoricalLoading, error: apiHistoricalError } = useFetchHistoricalIPData();

  // Use existing data if provided and showTimeInput is false
  useEffect(() => {
    if (!showTimeInput && existingData) {
      setData(existingData);
      // Notify parent component of data change
      if (onDataChange) {
        onDataChange(existingData);
      }
    }
  }, [existingData, showTimeInput, onDataChange]);

  // Function to calculate time range based on selected option
  const getTimeRange = () => {
    const now = Date.now();
    let startDate: number;
    let endDate: number = now;

    switch (selOption) {
      case "Last Hour":
        startDate = now - 3600000; // 1 hour ago
        break;
      case "Last Day":
        startDate = now - 86400000; // 1 day ago
        break;
      case "Last Week":
        startDate = now - 604800000; // 1 week ago
        break;
      case "Custom":
        if (customFrom && customTo) {
          startDate = new Date(customFrom).getTime();
          endDate = new Date(customTo).getTime();
          // Ensure startDate and endDate don't exceed current time
          if (startDate > now) {
            startDate = now;
          }
          if (endDate > now) {
            endDate = now;
          }
        } else {
          // Fallback to last day if custom dates are not set
          startDate = now - 86400000;
        }
        break;
      default:
        startDate = now - 86400000; // Default to last day
    }

    return { startDate, endDate };
  };

  // Function to fetch historical data for all servers
  const fetchHistoricalDataForPeriod = async () => {
    if (servers.length === 0 || !showTimeInput) return;

    // Don't fetch data if custom option is selected but both fields aren't filled
    if (selOption === "Custom" && (!customFrom || !customTo)) {
      return;
    }

    const { startDate, endDate } = getTimeRange();
    const startDateISO = dateFormatConversion(startDate);
    const endDateISO = dateFormatConversion(endDate);

    // console.log(`Fetching historical data for ${servers.length} servers from ${startDateISO} to ${endDateISO}`);

    const newData = new Map<string, NTPData[]>();

    // Fetch all servers in parallel instead of sequentially
    const fetchPromises = servers
      .filter(server => server.trim())
      .map(async (server) => {
        const historicalDataUrl = `${import.meta.env.VITE_SERVER_HOST_ADDRESS}/measurements/history/?server=${server}&start=${startDateISO}&end=${endDateISO}`;
        // console.log(`Fetching data for server: ${server}`);
        const historicalData = await fetchHistoricalData(historicalDataUrl);
        if (historicalData) {
          newData.set(server, historicalData);
          // console.log(`Successfully fetched ${historicalData.length} data points for ${server}`);
        } else {
          // console.warn(`Failed to fetch data for server: ${server}`);
        }
      });

    await Promise.all(fetchPromises);
    // console.log(`Completed fetching data for all servers`);
    setData(newData);
    // Notify parent component of data change
    if (onDataChange) {
      onDataChange(newData);
    }
  };

  // Fetch data when time period changes or servers change (only if showTimeInput is true)
  useEffect(() => {
    if (showTimeInput && servers.length > 0 && servers.some(s => s.trim())) {
      fetchHistoricalDataForPeriod();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selOption, customFrom, customTo, servers.join(','), showTimeInput]);

  const handleMeasurementChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onMeasurementChange(event.target.value as Measurement);
  };

  // Show loading state while fetching data (only if showTimeInput is true)
  if (showTimeInput && apiHistoricalLoading) {
    return (
      <div className="historical-data-chart">
        <div className="time-input-container">
          <TimeInput
            options={["Last Hour", "Last Day", "Last Week", "Custom"]}
            selectedOption={selOption}
            onSelectionChange={setSelOption}
            customFrom={customFrom}
            customTo={customTo}
            onFromChange={setCustomFrom}
            onToChange={setCustomTo}
          />
        </div>
        <div className="loading-div">
          <p>Loading historical data...</p>
          <LoadingSpinner size="large" />
        </div>
      </div>
    );
  }

  // Show error state if there's an error (only if showTimeInput is true)
  if (showTimeInput && apiHistoricalError) {
    return (
      <div className="historical-data-chart">
        <div className="time-input-container">
          <TimeInput
            options={["Last Hour", "Last Day", "Last Week", "Custom"]}
            selectedOption={selOption}
            onSelectionChange={setSelOption}
            customFrom={customFrom}
            customTo={customTo}
            onFromChange={setCustomFrom}
            onToChange={setCustomTo}
          />
        </div>
        <div className="error-div">
          <p>There was an error loading historical data.</p>
          <p>Please check the chosen time period.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="historical-data-chart">
      {showTimeInput && (
        <div className="time-input-container">
          <TimeInput
            options={["Last Hour", "Last Day", "Last Week", "Custom"]}
            selectedOption={selOption}
            onSelectionChange={setSelOption}
            customFrom={customFrom}
            customTo={customTo}
            onFromChange={setCustomFrom}
            onToChange={setCustomTo}
          />
        </div>
      )}

      <div className="measurement-toggle">
        <input
          type="radio"
          id="offset"
          name="measurement"
          value="offset"
          checked={selectedMeasurement === 'offset'}
          onChange={handleMeasurementChange}
        />
        <label htmlFor="offset">Offset</label>

        <input
          type="radio"
          id="rtt"
          name="measurement"
          value="RTT"
          checked={selectedMeasurement === 'RTT'}
          onChange={handleMeasurementChange}
        />
        <label htmlFor="rtt">Round-trip time</label>
      </div>

      <div className="chart-container">
        <LineChart
          data={data}
          selectedMeasurement={selectedMeasurement}
          selectedOption={showTimeInput ? selOption : "Last Day"}
          customRange={showTimeInput ? { from: customFrom, to: customTo } : undefined}
          legendDisplay={legendDisplay}
        />
      </div>
    </div>
  );
}
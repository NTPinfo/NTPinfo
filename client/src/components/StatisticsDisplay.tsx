import React from 'react';
import { NTPData } from '../utils/types';
import { Measurement } from '../utils/types';

interface StatisticsDisplayProps {
  data: Map<string, NTPData[]> | null;
  selectedMeasurement: Measurement;
}

const StatisticsDisplay: React.FC<StatisticsDisplayProps> = ({
  data,
  selectedMeasurement,
}) => {
  if (!data) return null;

  const calculateStats = (serverData: NTPData[]) => {
    if (!serverData || serverData.length === 0) {
      return {
        min: "N/A",
        max: "N/A",
        avg: "N/A",
      };
    }

    const validValues = serverData
      .map(d => {
        if (selectedMeasurement === "RTT") {
          return d.RTT;
        } else {
          return d.offset;
        }
      })
      .filter((value): value is number => 
        value !== null && 
        value !== undefined && 
        typeof value === 'number' &&
        !isNaN(value) && 
        isFinite(value)
      );

    // show N/A if there are no values to show
    if (validValues.length === 0) {
      return {
        min: "N/A",
        max: "N/A",
        avg: "N/A",
      };
    }

    const min = Math.min(...validValues);
    const max = Math.max(...validValues);
    const avg = validValues.reduce((a, b) => a + b, 0) / validValues.length;

    return {
      min: min.toFixed(3),
      max: max.toFixed(3),
      avg: avg.toFixed(3),
    };
  };

  return (
    <div className="statistics-container">
      {Array.from(data.entries()).map(([server, serverData]) => {
        const stats = calculateStats(serverData);

        return (
          <div key={server} className="server-stats">
            <h3>{server}</h3>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">Min:</span>
                <span className="stat-value">{stats.min}{stats.min !== "N/A" ? " ms" : ""}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Max:</span>
                <span className="stat-value">{stats.max}{stats.max !== "N/A" ? " ms" : ""}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Average:</span>
                <span className="stat-value">{stats.avg}{stats.avg !== "N/A" ? " ms" : ""}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default StatisticsDisplay
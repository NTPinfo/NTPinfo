import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';
import { StatisticsData } from '../hooks/useFetchStatistics';
import '../styles/StatisticsVisualization.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

ChartJS.defaults.color = 'rgba(70, 70, 70)';

interface StatisticsVisualizationProps {
  data: StatisticsData;
}

const StatisticsVisualization: React.FC<StatisticsVisualizationProps> = ({ data }) => {
  // Bar chart data for measurement counts
  const measurementCountsData = {
    labels: ['Domain Name', 'IP Address', 'NTS', 'RIPE Atlas'],
    datasets: [
      {
        label: 'Number of Measurements',
        data: [
          data.dn_measurements_count,
          data.ip_measurements_count,
          data.nts_measurements_count,
          data.ripe_measurements_count,
        ],
        backgroundColor: [
          'rgba(0, 33, 84, 0.8)',
          'rgba(25, 97, 172, 0.8)',
          'rgba(82, 176, 112, 0.8)',
          'rgba(232, 84, 34, 0.8)',
        ],
        borderColor: [
          'rgba(0, 33, 84, 1)',
          'rgba(25, 97, 172, 1)',
          'rgba(82, 176, 112, 1)',
          'rgba(232, 84, 34, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  // Bar chart options
  const measurementCountsOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Measurement Types Overview',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
        color: 'rgba(70, 70, 70)',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          precision: 0,
        },
      },
    },
  };

  // NTP Versions analysis data
  const ntpVersionsLabels = ['NTPv1', 'NTPv2', 'NTPv3', 'NTPv4', 'NTPv5'];
  const ntpVersionsAnalyzed = [
    data.ntp_versions_analyzed_count.analyzed_ntpv1,
    data.ntp_versions_analyzed_count.analyzed_ntpv2,
    data.ntp_versions_analyzed_count.analyzed_ntpv3,
    data.ntp_versions_analyzed_count.analyzed_ntpv4,
    data.ntp_versions_analyzed_count.analyzed_ntpv5,
  ];

  const ntpVersionsData = {
    labels: ntpVersionsLabels,
    datasets: [
      {
        label: 'Analyzed',
        data: ntpVersionsAnalyzed,
        backgroundColor: [
          'rgba(0, 33, 84, 0.7)',
          'rgba(25, 97, 172, 0.7)',
          'rgba(82, 176, 112, 0.7)',
          'rgba(232, 84, 34, 0.7)',
          'rgba(229, 146, 54, 0.7)',
        ],
        borderColor: [
          'rgba(0, 33, 84, 1)',
          'rgba(25, 97, 172, 1)',
          'rgba(82, 176, 112, 1)',
          'rgba(232, 84, 34, 1)',
          'rgba(229, 146, 54, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const ntpVersionsOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'NTP Versions Analysis Count',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
        color: 'rgba(70, 70, 70)',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          precision: 0,
        },
      },
    },
  };

  // Success rates pie chart
  const successRatesData = {
    labels: ntpVersionsLabels,
    datasets: [
      {
        label: 'Success Rate (%)',
        data: [
          data.ntp_versions_analyzed_count.success_rate_ntpv1 * 100,
          data.ntp_versions_analyzed_count.success_rate_ntpv2 * 100,
          data.ntp_versions_analyzed_count.success_rate_ntpv3 * 100,
          data.ntp_versions_analyzed_count.success_rate_ntpv4 * 100,
          data.ntp_versions_analyzed_count.success_rate_ntpv5 * 100,
        ],
        backgroundColor: [
          'rgba(0, 33, 84, 0.7)',
          'rgba(25, 97, 172, 0.7)',
          'rgba(82, 176, 112, 0.7)',
          'rgba(232, 84, 34, 0.7)',
          'rgba(229, 146, 54, 0.7)',
        ],
        borderColor: [
          'rgba(0, 33, 84, 1)',
          'rgba(25, 97, 172, 1)',
          'rgba(82, 176, 112, 1)',
          'rgba(232, 84, 34, 1)',
          'rgba(229, 146, 54, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const successRatesOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          padding: 15,
          font: {
            size: 12,
          },
        },
      },
      title: {
        display: true,
        text: 'NTP Versions Success Rates',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
        color: 'rgba(70, 70, 70)',
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `${context.label}: ${context.parsed.toFixed(1)}%`;
          },
        },
      },
    },
  };

  return (
    <div className="statistics-visualization">
      <div className="statistics-grid">
        <div className="statistics-card">
          <div className="statistics-chart-container">
            <Bar data={measurementCountsData} options={measurementCountsOptions} />
          </div>
        </div>
        <div className="statistics-card">
          <div className="statistics-chart-container">
            <Bar data={ntpVersionsData} options={ntpVersionsOptions} />
          </div>
        </div>
        <div className="statistics-card">
          <div className="statistics-chart-container">
            <Pie data={successRatesData} options={successRatesOptions} />
          </div>
        </div>
      </div>
      <div className="statistics-summary">
        <div className="statistic-item">
          <span className="statistic-label">Total Domain Measurements:</span>
          <span className="statistic-value">{data.dn_measurements_count.toLocaleString()}</span>
        </div>
        <div className="statistic-item">
          <span className="statistic-label">Total IP Measurements:</span>
          <span className="statistic-value">{data.ip_measurements_count.toLocaleString()}</span>
        </div>
        <div className="statistic-item">
          <span className="statistic-label">Total NTS Measurements:</span>
          <span className="statistic-value">{data.nts_measurements_count.toLocaleString()}</span>
        </div>
        <div className="statistic-item">
          <span className="statistic-label">Total RIPE Atlas Measurements:</span>
          <span className="statistic-value">{data.ripe_measurements_count.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
};

export default StatisticsVisualization;


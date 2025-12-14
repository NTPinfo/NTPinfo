import React from 'react';
import '../styles/AboutTab.css';
import Header from '../components/Header';
import DataAnalysis from '../assets/chart-svgrepo-com.png';
import Visualization from '../assets/graph-svgrepo-com.png';
import Comparison from '../assets/scale-unbalanced-svgrepo-com.png';
import StatisticsVisualization from '../components/StatisticsVisualization';
import { useFetchStatistics } from '../hooks/useFetchStatistics';
import LoadingSpinner from '../components/LoadingSpinner';

const AboutTab: React.FC = () => {
  const { data: statistics, loading: statisticsLoading, error: statisticsError } = useFetchStatistics();

  return (
    <div className="about-tab">
      <Header />
      <div className="about-section">
        <h1>Welcome to NTPInfo</h1>
        <p className="about-subtitle">
          An open-source platform for comprehensive Network Time Protocol (NTP) server analysis and measurement.
        </p>

        <div className="about-project-info">
          <h2>About Our Project</h2>
          <p>
            NTPinfo is an open-source platform for measuring <strong>NTP</strong> (Network Time Protocol) and 
            <strong> NTS</strong> (Network Time Security) clock synchronization. It provides detailed insights 
            into time synchronization accuracy across the Internet, supporting researchers and network operators 
            in understanding and improving timekeeping reliability.
          </p>
          
          <p>
            This project originated as part of the <strong>CSE2000 Software Project</strong> course at 
            <strong> Delft University of Technology (TU Delft)</strong>, developed by five Computer Science 
            and Engineering students: <strong>George-Matei Andrei</strong>, <strong>Horia-Andrei Botezatu</strong>, 
            <strong> Mihai-Valentin Nicolae</strong>, <strong>Călin-Mihai Olaru</strong>, and <strong>Șerban Orza</strong>.
          </p>

          <p>
            We are collaborating with <strong>TU Delft</strong> and <strong>SIDN Labs</strong>, with 
            <strong> Dr. Giovane Moura</strong> serving as our mentor and advisor. <strong>SIDN Labs</strong> hosts 
            the NTPinfo platform and provides ongoing support for our project.
          </p>

          <p>
            The platform enables comprehensive NTP server analysis, including offset measurements, round-trip 
            time (RTT) analysis, Network Time Security (NTS) evaluation, NTP version compatibility testing, 
            and distributed measurements through RIPE Atlas integration. Recent developments include enhanced 
            NTS and NTP versions analysis capabilities, contributing to the detection of security risks and 
            strengthening Internet infrastructure globally.
          </p>

          <p>
            NTPinfo has been presented at both <strong>ICANN 84</strong> and <strong>RIPE 91</strong>, where 
            we discussed the role of time synchronization in online systems and engaged with the community on 
            topics such as network reliability and measurement accuracy.
          </p>
        </div>

        <div className="about-features">
          <div className="feature">
            <span className="feature-icon"><img src={DataAnalysis} alt="Data Analysis" /></span>
            <h3>Measurement Analysis</h3>
            <p>Analyze different metrics to determine the accuracy of NTP servers</p>
          </div>
          <div className="feature">
            <span className="feature-icon"><img src={Visualization} alt="Visualization" /></span>
            <h3>Visualization</h3>
            <p>Interactive graphs for better understanding of NTP data</p>
          </div>
          <div className="feature">
            <span className="feature-icon"><img src={Comparison} alt="Comparison" /></span>
            <h3>Comparison</h3>
            <p>Compare different servers to gain deeper insights</p>
          </div>
        </div>

        <div className="statistics-section">
          <h2>Platform Statistics</h2>
          <p className="statistics-description">
            Real-time statistics from our measurement database, providing insights into the scale and diversity 
            of NTP server analysis conducted through our platform.
          </p>
          {statisticsLoading && (
            <div className="statistics-loading">
              <LoadingSpinner size="large" />
            </div>
          )}
          {statisticsError && (
            <div className="statistics-error">
              <p>Unable to load statistics. Please try again later.</p>
            </div>
          )}
          {!statisticsLoading && !statisticsError && statistics && (
            <StatisticsVisualization data={statistics} />
          )}
        </div>
      </div>
    </div>
  );
};

export default AboutTab
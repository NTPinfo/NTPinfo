import React from 'react';
import { NTSResult } from '../utils/types';
import '../styles/NTSResultBox.css';

interface NTSResultBoxProps {
  ntsResult: NTSResult | null;
  loading?: boolean;
  error?: Error | null;
}

const NTSResultBox: React.FC<NTSResultBoxProps> = ({ ntsResult, loading, error }) => {
  if (loading) {
    return (
      <div className="nts-result-box">
        <div className="nts-label">NTS Measurement</div>
        <div className="nts-loading">
          <p>Loading NTS measurement...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="nts-result-box nts-error">
        <div className="nts-label">NTS Measurement</div>
        <div className="nts-error-content">
          <p>Error: {error.message}</p>
        </div>
      </div>
    );
  }

  if (!ntsResult) {
    return null;
  }

  const formatNTSValue = (value: any): string => {
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  const getNTSStatus = (): { status: string; color: string } => {
    // Check for NTS success based on the actual backend response structure
    if (ntsResult['NTS succeeded'] === true) {
      return { status: 'NTS Supported', color: 'success' };
    }
    if (ntsResult['NTS succeeded'] === false) {
      return { status: 'NTS Not Supported', color: 'warning' };
    }
    if (ntsResult.error || ntsResult.failed) {
      return { status: 'NTS Error', color: 'error' };
    }
    return { status: 'NTS Available', color: 'info' };
  };

  const ntsStatus = getNTSStatus();

  // Show only the most important fields in a compact format
  const showFields = ['NTS analysis', 'Host', 'Measured server IP'];
  const hasMoreFields = Object.keys(ntsResult).length > showFields.length + 1; // +1 for 'NTS succeeded'

  return (
    <div className="nts-result-box">
      <div className="nts-label">NTS Measurement</div>
      <div className="nts-content">
        <div className={`nts-status nts-status-${ntsStatus.color}`}>
          {ntsStatus.status}
        </div>
        
        {/* Show key fields in compact format */}
        <div className="nts-details">
          {showFields
            .filter(key => ntsResult[key] !== undefined && ntsResult[key] !== null)
            .map((key) => (
              <div key={key} className="nts-metric">
                <span className="nts-key">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                <span className="nts-value">{formatNTSValue(ntsResult[key])}</span>
              </div>
            ))}
        </div>

        {/* Show additional details in a collapsible section if there are more fields */}
        {hasMoreFields && (
          <details className="nts-other-details">
            <summary>More Details</summary>
            <div className="nts-details">
              {Object.keys(ntsResult)
                .filter(key => !showFields.includes(key) && key !== 'NTS succeeded')
                .map((key) => (
                  <div key={key} className="nts-metric">
                    <span className="nts-key">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                    <span className="nts-value">{formatNTSValue(ntsResult[key])}</span>
                  </div>
                ))}
            </div>
          </details>
        )}
      </div>
    </div>
  );
};

export default NTSResultBox;

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

  // Normalize keys to support both backend snake_case and display Title Case keys
  const normalize = (src: any | null): Record<string, any> => {
    if (!src) return {};
    const map: Record<string, string> = {
      nts_succeeded: 'NTS succeeded',
      nts_analysis: 'NTS analysis',
      host: 'Host',
      measured_server_ip: 'Measured server IP',
      measured_server_port: 'Measured server Port',
      rtt: 'RTT (s)',
      offset: 'Offset (s)',
      stratum: 'Stratum',
      poll: 'Poll',
      precision: 'Precision',
      root_delay: 'Root delay',
      root_disp: 'Root dispersion',
      root_dist: 'Root distance',
      kiss_code: 'Kiss code',
      ref_id: 'Ref ID',
      ref_id_raw: 'Ref ID Raw',
      nts_measurement_version: 'NTS version',
      warning_ip: 'Warning'
    };
    const out: Record<string, any> = {};
    for (const [k, v] of Object.entries(src)) {
      out[map[k] ?? k] = v;
    }
    return out;
  };

  const data = normalize(ntsResult);

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
    // Consider both normalized and snake_case keys, but rely on normalized map
    const succeeded = data['NTS succeeded'] === true || (data as any)['nts_succeeded'] === true;
    const failed = data['NTS succeeded'] === false || (data as any)['nts_succeeded'] === false;

    if (succeeded) {
      return { status: 'NTS Supported', color: 'success' };
    }
    if (failed) {
      return { status: 'NTS Not Supported', color: 'warning' };
    }
    if ((data as any).error || (data as any).failed) {
      return { status: 'NTS Error', color: 'error' };
    }
    // If no data present at all
    if (Object.keys(data).length === 0) {
      return { status: 'NTS Not Available', color: 'info' };
    }
    return { status: 'NTS Available', color: 'info' };
  };

  const ntsStatus = getNTSStatus();

  // Show only the most important fields in a compact format
  const showFields = ['NTS analysis', 'Host', 'Measured server IP'];
  const hasMoreFields = Object.keys(data).length > showFields.length + 1; // +1 for 'NTS succeeded'

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
            .filter(key => data[key] !== undefined && data[key] !== null)
            .map((key) => (
              <div key={key} className="nts-metric">
                <span className="nts-key">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                <span className="nts-value">{formatNTSValue(data[key])}</span>
              </div>
            ))}
        </div>

        {/* Show additional details in a collapsible section if there are more fields */}
        {hasMoreFields && (
          <details className="nts-other-details">
            <summary>More Details</summary>
            <div className="nts-details">
              {Object.keys(data)
                .filter(key => !showFields.includes(key) && key !== 'NTS succeeded')
                .map((key) => (
                  <div key={key} className="nts-metric">
                    <span className="nts-key">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                    <span className="nts-value">{formatNTSValue(data[key])}</span>
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

import { useState } from 'react';
import { MeasurementRequest } from '../utils/types';
import '../styles/MeasurementSettings.css';

interface MeasurementSettingsProps {
  settings: MeasurementRequest;
  onSettingsChange: (settings: MeasurementRequest) => void;
  disabled?: boolean;
}

const NTP_VERSIONS = [
  { value: 'ntpv1', label: 'NTPv1' },
  { value: 'ntpv2', label: 'NTPv2' },
  { value: 'ntpv3', label: 'NTPv3' },
  { value: 'ntpv4', label: 'NTPv4' },
  { value: 'ntpv5', label: 'NTPv5' },
];

const MEASUREMENT_TYPES = [
  { value: 'ntpv1', label: 'NTPv1' },
  { value: 'ntpv2', label: 'NTPv2' },
  { value: 'ntpv3', label: 'NTPv3' },
  { value: 'ntpv4', label: 'NTPv4' },
  { value: 'ntpv5', label: 'NTPv5' },
];

const NTPV5_DRAFTS = [
  { value: 'draft-ietf-ntp-ntpv5-06', label: 'draft-ietf-ntp-ntpv5-06' },
  { value: 'draft-ietf-ntp-ntpv5-05', label: 'draft-ietf-ntp-ntpv5-05' },
  { value: 'custom', label: 'Custom...' },
];

export default function MeasurementSettings({ settings, onSettingsChange, disabled = false }: MeasurementSettingsProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showCustomInput, setShowCustomInput] = useState(false);
  
  const showNtpv5Draft = settings.measurement_type === 'ntpv5' || 
    (settings.ntp_versions_to_analyze && settings.ntp_versions_to_analyze.includes('ntpv5')) ||
    settings.analyse_all_ntp_versions === true;
  
  // Determine current draft value and if custom input should be shown
  const currentDraft = settings.ntpv5_draft || 'draft-ietf-ntp-ntpv5-06';
  const predefinedDrafts = NTPV5_DRAFTS.filter(d => d.value !== 'custom').map(d => d.value);
  const isCustomDraft = currentDraft !== 'custom' && !predefinedDrafts.includes(currentDraft);
  const shouldShowCustomInput = showCustomInput || isCustomDraft;

  const updateSetting = <K extends keyof MeasurementRequest>(key: K, value: MeasurementRequest[K]) => {
    // Convert empty strings to undefined for optional fields
    const cleanedValue = (typeof value === 'string' && value.trim() === '') ? undefined : value;
    const updated = { ...settings, [key]: cleanedValue };
    
    // Auto-set analyse_all_ntp_versions if all versions are selected
    if (key === 'ntp_versions_to_analyze') {
      const selectedVersions = cleanedValue as string[] | null;
      const allVersionsSelected = selectedVersions && selectedVersions.length === NTP_VERSIONS.length;
      if (allVersionsSelected) {
        updated.analyse_all_ntp_versions = true;
        // When analyse_all_ntp_versions is true, clear ntp_versions_to_analyze to avoid confusion
        updated.ntp_versions_to_analyze = undefined;
      } else {
        // When not all versions are selected, set analyse_all_ntp_versions to false
        updated.analyse_all_ntp_versions = false;
      }
    }
    
    onSettingsChange(updated);
  };

  const toggleNtpVersion = (version: string) => {
    // If analyse_all_ntp_versions is true, start with all versions
    // Otherwise, use the current list (or empty array if none)
    const current = settings.analyse_all_ntp_versions 
      ? NTP_VERSIONS.map(v => v.value)
      : (settings.ntp_versions_to_analyze || []);
    
    const updated = current.includes(version)
      ? current.filter(v => v !== version)
      : [...current, version];
    updateSetting('ntp_versions_to_analyze', updated.length > 0 ? updated : null);
  };

  return (
    <div className="measurement-settings">
      <button
        type="button"
        className="settings-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        disabled={disabled}
        aria-expanded={isExpanded}
      >
        <span className="settings-toggle-icon">{isExpanded ? '▼' : '▶'}</span>
        <span className="settings-toggle-text">Advanced Settings</span>
      </button>

      {isExpanded && (
        <div className="settings-content">
          <div className="settings-grid">
            {/* Measurement Type */}
            <div className="settings-row">
              <label htmlFor="measurement_type" className="settings-label-compact">
                Measurement Type
                <span className="settings-tooltip" title="Specify the NTP protocol version to use for measurement.">?</span>
              </label>
              <select
                id="measurement_type"
                value={settings.measurement_type || 'ntpv4'}
                onChange={(e) => updateSetting('measurement_type', e.target.value || 'ntpv4')}
                disabled={disabled}
                className="settings-select-compact"
              >
                {MEASUREMENT_TYPES.map(type => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </div>

            {/* NTP Versions to Analyze */}
            <div className="settings-row">
              <label className="settings-label-compact">
                NTP Versions to Analyze
                <span className="settings-tooltip" title="Choose which NTP protocol versions to test. Selecting all versions automatically enables 'analyze all'.">?</span>
              </label>
              <div className="settings-checkbox-group-compact">
                {NTP_VERSIONS.map(version => {
                  // If analyse_all_ntp_versions is true, all checkboxes should be checked
                  // Otherwise, check if the version is in the ntp_versions_to_analyze list
                  const isChecked = settings.analyse_all_ntp_versions 
                    ? true 
                    : (settings.ntp_versions_to_analyze || []).includes(version.value);
                  
                  return (
                    <label key={version.value} className="settings-checkbox-label-compact">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggleNtpVersion(version.value)}
                        disabled={disabled}
                        className="settings-checkbox"
                      />
                      <span>{version.label}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* NTPv5 Draft */}
            {showNtpv5Draft && (
              <>
                <div className="settings-row">
                  <label htmlFor="ntpv5_draft" className="settings-label-compact">
                    NTPv5 Draft
                    <span className="settings-tooltip" title="Specify which NTPv5 draft specification to use for testing.">?</span>
                  </label>
                  <select
                    id="ntpv5_draft"
                    value={isCustomDraft ? 'custom' : currentDraft}
                    onChange={(e) => {
                      if (e.target.value === 'custom') {
                        // When selecting custom, show the input field
                        setShowCustomInput(true);
                        // Preserve existing custom value if it exists, otherwise leave undefined
                        if (isCustomDraft) {
                          updateSetting('ntpv5_draft', currentDraft);
                        }
                      } else {
                        setShowCustomInput(false);
                        updateSetting('ntpv5_draft', e.target.value);
                      }
                    }}
                    disabled={disabled}
                    className="settings-select-compact"
                  >
                    {NTPV5_DRAFTS.map(draft => (
                      <option key={draft.value} value={draft.value}>{draft.label}</option>
                    ))}
                  </select>
                </div>
                {shouldShowCustomInput && (
                  <div className="settings-row">
                    <label htmlFor="custom_ntpv5_draft" className="settings-label-compact">
                      Custom Draft Name
                      <span className="settings-tooltip" title="Enter a custom NTPv5 draft name (max 50 characters).">?</span>
                    </label>
                    <input
                      id="custom_ntpv5_draft"
                      type="text"
                      value={isCustomDraft ? currentDraft : ''}
                      onChange={(e) => {
                        const value = e.target.value.slice(0, 50);
                        updateSetting('ntpv5_draft', value.trim() || undefined);
                        if (value.trim()) {
                          setShowCustomInput(true);
                        }
                      }}
                      disabled={disabled}
                      placeholder="Enter custom draft name"
                      className="settings-input-compact"
                      maxLength={50}
                    />
                  </div>
                )}
              </>
            )}

            {/* Checkboxes */}
            {/* 
            <div className="settings-row">
              <label className="settings-checkbox-label-compact">
                <input
                  type="checkbox"
                  checked={settings.ntp_versions_analysis_on_each_ip || false}
                  onChange={(e) => updateSetting('ntp_versions_analysis_on_each_ip', e.target.checked || undefined)}
                  disabled={disabled}
                  className="settings-checkbox"
                />
                <span>NTP versions on each IP</span>
                <span className="settings-tooltip" title="When measuring a domain name, perform NTP version analysis on each IP address separately.">?</span>
              </label>
              <label className="settings-checkbox-label-compact">
                <input
                  type="checkbox"
                  checked={settings.nts_analysis_on_each_ip || false}
                  onChange={(e) => updateSetting('nts_analysis_on_each_ip', e.target.checked || undefined)}
                  disabled={disabled}
                  className="settings-checkbox"
                />
                <span>NTS analysis on each IP</span>
                <span className="settings-tooltip" title="When measuring a domain name, perform NTS (Network Time Security) analysis on each IP address separately.">?</span>
              </label>
            </div>
            */}

            {/* RIPE Probes */}
            <div className="settings-row">
              <label htmlFor="custom_probes_asn" className="settings-label-compact">
                Probe ASN
                <span className="settings-tooltip" title="Autonomous System Number (ASN) for RIPE Atlas probes.">?</span>
              </label>
              <input
                id="custom_probes_asn"
                type="text"
                value={settings.custom_probes_asn || ''}
                onChange={(e) => updateSetting('custom_probes_asn', e.target.value || undefined)}
                disabled={disabled}
                placeholder="AS12345"
                className="settings-input-compact"
              />
            </div>

            <div className="settings-row">
              <label htmlFor="custom_probes_country" className="settings-label-compact">
                Probe Country
                <span className="settings-tooltip" title="Country code (ISO 3166-1 alpha-2) for RIPE Atlas probes.">?</span>
              </label>
              <input
                id="custom_probes_country"
                type="text"
                value={settings.custom_probes_country || ''}
                onChange={(e) => updateSetting('custom_probes_country', e.target.value || undefined)}
                disabled={disabled}
                placeholder="NL, US, DE"
                className="settings-input-compact"
                maxLength={2}
              />
            </div>

            <div className="settings-row">
              <label htmlFor="custom_client_ip" className="settings-label-compact">
                Client IP
                <span className="settings-tooltip" title="IP address to select RIPE Atlas probes close to that location.">?</span>
              </label>
              <input
                id="custom_client_ip"
                type="text"
                value={settings.custom_client_ip || ''}
                onChange={(e) => updateSetting('custom_client_ip', e.target.value || undefined)}
                disabled={disabled}
                placeholder="8.8.8.8"
                className="settings-input-compact"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


import React, { useState, useMemo } from 'react';
import '../styles/SearchTab.css';
import Header from '../components/Header';

interface SearchResult {
  id: string;
  server: string;
  ip: string;
  asn: string;
  country: string;
  offset: number;
  rtt: number;
  stratum: number;
  lastMeasured: string;
  measurementId: string;
  hasNTS: boolean;
  supportedVersions: string[];
  measurementType: string;
  ipVersion: 4 | 6;
}

type SortField = 'offset' | 'rtt' | 'stratum' | 'lastMeasured' | 'server';
type SortOrder = 'asc' | 'desc';
type SearchType = 'ip-domain' | 'id';

const SearchTab: React.FC = () => {
  const [searchType, setSearchType] = useState<SearchType>('ip-domain');
  const [isAdvancedExpanded, setIsAdvancedExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [sortField, setSortField] = useState<SortField>('lastMeasured');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const resultsPerPage = 32;

  const [searchQuery, setSearchQuery] = useState('');
  const [measurementIdQuery, setMeasurementIdQuery] = useState('');

  const [measurementType, setMeasurementType] = useState<string>('');
  const [referenceIdFilter, setReferenceIdFilter] = useState('');
  const [ntpv5DraftFilter, setNtpv5DraftFilter] = useState<string>('');
  const [showCustomDraftInput, setShowCustomDraftInput] = useState(false);
  const [customDraftFilter, setCustomDraftFilter] = useState('');
  const [asnFilter, setAsnFilter] = useState('');
  const [countryFilter, setCountryFilter] = useState('');
  const [ipVersionFilter, setIpVersionFilter] = useState<string>('');
  const [stratumFilter, setStratumFilter] = useState('');
  const [ntsFilter, setNtsFilter] = useState<string>('');
  const [versionFilter, setVersionFilter] = useState<string[]>([]);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [usePresent, setUsePresent] = useState(false);
  const [offsetMin, setOffsetMin] = useState('');
  const [offsetMax, setOffsetMax] = useState('');

  // it is just a method to generate dummy data, as we are testing the UI (will remove it soon)
  const generateDummyResults = (count: number = 150): SearchResult[] => {
    const countries = ['NL', 'US', 'DE', 'GB', 'FR', 'JP', 'CA', 'AU', 'SE', 'CH', 'IT', 'ES', 'BR', 'IN', 'CN'];
    const versions = ['NTPv1', 'NTPv2', 'NTPv3', 'NTPv4', 'NTPv5'];
    const servers = [
      'time.google.com', 'time.cloudflare.com', 'time.windows.com', 
      'pool.ntp.org', 'ntp.example.com', 'time.nist.gov', 'ntp1.inrim.it'
    ];
    const measurementTypes = ['ntpv1', 'ntpv2', 'ntpv3', 'ntpv4', 'ntpv5'];
    
    return Array.from({ length: count }, (_, i) => ({
      id: `result-${i + 1}`,
      server: `${servers[i % servers.length]}${i > servers.length ? `-${i}` : ''}`,
      ip: `203.0.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
      asn: `AS${Math.floor(Math.random() * 90000) + 1000}`,
      country: countries[Math.floor(Math.random() * countries.length)],
      offset: parseFloat((Math.random() * 200 - 100).toFixed(3)),
      rtt: parseFloat((Math.random() * 100 + 10).toFixed(2)),
      stratum: Math.floor(Math.random() * 4) + 1,
      lastMeasured: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      measurementId: Math.random() > 0.5 ? `dn${Math.floor(Math.random() * 10000)}` : `ip${Math.floor(Math.random() * 10000)}`,
      hasNTS: Math.random() > 0.5,
      supportedVersions: versions.slice(0, Math.floor(Math.random() * 4) + 1),
      measurementType: measurementTypes[Math.floor(Math.random() * measurementTypes.length)],
      ipVersion: Math.random() > 0.5 ? 4 : 6,
    }));
  };

  const handleSearch = async () => {
    setLoading(true);
    setHasSearched(true);
    setCurrentPage(1);
    
    setTimeout(() => {
      let resultCount = 150;
      if (searchType === 'ip-domain') {
        if (searchQuery.trim()) {
          resultCount = Math.floor(Math.random() * 100) + 10;
        } else if (hasActiveFilters()) {
          // search by filters only
          resultCount = Math.floor(Math.random() * 200) + 50;
        } else {
          // no query and no filters (shouldn't happen due to disabled button, but handle it)
          resultCount = 0;
        }
      } else if (searchType === 'id' && measurementIdQuery.trim()) {
        resultCount = 1;
      }
      
      const allResults = resultCount > 0 ? generateDummyResults(resultCount) : [];
      setResults(allResults);
      setLoading(false);
    }, 800);
  };

  const handleVersionToggle = (version: string) => {
    setVersionFilter(prev => 
      prev.includes(version) 
        ? prev.filter(v => v !== version)
        : [...prev, version]
    );
  };

  const formatDateForInput = (date: Date): string => {
    return date.toISOString().split('T')[0];
  };

  const clearFilters = () => {
    setSearchQuery('');
    setMeasurementIdQuery('');
    setMeasurementType('');
    setReferenceIdFilter('');
    setNtpv5DraftFilter('');
    setCustomDraftFilter('');
    setShowCustomDraftInput(false);
    setAsnFilter('');
    setCountryFilter('');
    setIpVersionFilter('');
    setStratumFilter('');
    setNtsFilter('');
    setVersionFilter([]);
    setDateFrom('');
    setDateTo('');
    setUsePresent(false);
    setOffsetMin('');
    setOffsetMax('');
    setResults([]);
    setHasSearched(false);
    setCurrentPage(1);
    setIsAdvancedExpanded(false);
  };

  const hasActiveFilters = () => {
    return !!(
      measurementType ||
      referenceIdFilter.trim() ||
      ntpv5DraftFilter ||
      customDraftFilter.trim() ||
      asnFilter.trim() ||
      countryFilter.trim() ||
      ipVersionFilter ||
      stratumFilter ||
      ntsFilter ||
      versionFilter.length > 0 ||
      dateFrom ||
      dateTo ||
      usePresent ||
      offsetMin ||
      offsetMax
    );
  };

  const isSearchDisabled = () => {
    if (searchType === 'ip-domain') {
      return !searchQuery.trim() && !hasActiveFilters();
    } else {
      return !measurementIdQuery.trim();
    }
  };

  const sortedResults = useMemo(() => {
    const sorted = [...results].sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];

      if (sortField === 'lastMeasured') {
        aVal = new Date(a.lastMeasured).getTime();
        bVal = new Date(b.lastMeasured).getTime();
      }

      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [results, sortField, sortOrder]);

  // pagination
  const totalPages = Math.ceil(sortedResults.length / resultsPerPage);
  const startIndex = (currentPage - 1) * resultsPerPage;
  const endIndex = startIndex + resultsPerPage;
  const paginatedResults = sortedResults.slice(startIndex, endIndex);

  const MEASUREMENT_TYPES = [
    { value: '', label: 'Any' },
    { value: 'ntpv1', label: 'NTPv1' },
    { value: 'ntpv2', label: 'NTPv2' },
    { value: 'ntpv3', label: 'NTPv3' },
    { value: 'ntpv4', label: 'NTPv4' },
    { value: 'ntpv5', label: 'NTPv5' },
  ];

  const NTP_VERSIONS = [
    { value: 'NTPv1', label: 'NTPv1' },
    { value: 'NTPv2', label: 'NTPv2' },
    { value: 'NTPv3', label: 'NTPv3' },
    { value: 'NTPv4', label: 'NTPv4' },
    { value: 'NTPv5', label: 'NTPv5' },
  ];

  const NTPV5_DRAFTS = [
    { value: 'draft-ietf-ntp-ntpv5-06', label: 'draft-ietf-ntp-ntpv5-06' },
    { value: 'draft-ietf-ntp-ntpv5-05', label: 'draft-ietf-ntp-ntpv5-05' },
    { value: 'custom', label: 'Custom...' },
  ];

  // Determine if NTPv5 draft field should be shown
  const showNtpv5Draft = measurementType === 'ntpv5' || versionFilter.includes('NTPv5');
  
  // Determine current draft value and if custom input should be shown
  const predefinedDrafts = NTPV5_DRAFTS.filter(d => d.value !== 'custom').map(d => d.value);
  const currentDraft = ntpv5DraftFilter || 'draft-ietf-ntp-ntpv5-06';
  const isCustomDraft = currentDraft !== 'custom' && !predefinedDrafts.includes(currentDraft) && customDraftFilter !== '';
  const shouldShowCustomInput = showCustomDraftInput || isCustomDraft;

  return (
    <div className="search-tab">
      <Header />
      <div className="search-container">
        <div className="search-header">
          <h1>Search Measurements</h1>
        </div>

        <div className="search-main-panel">
          <div className="search-type-tabs">
            <button
              type="button"
              className={`search-type-tab ${searchType === 'ip-domain' ? 'active' : ''}`}
              onClick={() => {
                setSearchType('ip-domain');
                setMeasurementIdQuery('');
                if (hasSearched) {
                  setResults([]);
                  setHasSearched(false);
                }
              }}
            >
              IP / Domain Name
            </button>
            <button
              type="button"
              className={`search-type-tab ${searchType === 'id' ? 'active' : ''}`}
              onClick={() => {
                setSearchType('id');
                setSearchQuery('');
                setIsAdvancedExpanded(false);
                if (hasSearched) {
                  setResults([]);
                  setHasSearched(false);
                }
              }}
            >
              Measurement ID
            </button>
          </div>

          {searchType === 'ip-domain' ? (
            <>
              <div className="main-search-row">
                <label htmlFor="main-search" className="main-search-label">
                  Search by IP or Domain Name
                </label>
                <div className="main-search-input-wrapper">
                  <input
                    id="main-search"
                    type="text"
                    className="main-search-input"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="e.g., time.google.com or 8.8.8.8 (leave empty to use filters only)"
                    onKeyDown={(e) => e.key === 'Enter' && !loading && !isSearchDisabled() && handleSearch()}
                  />
                  <button
                    className="search-submit-button"
                    onClick={handleSearch}
                    disabled={loading || isSearchDisabled()}
                  >
                    {loading ? 'Searching...' : 'Search'}
                  </button>
                </div>
              </div>

              <div className="advanced-settings-section">
            <button
              type="button"
              className="advanced-toggle"
              onClick={() => setIsAdvancedExpanded(!isAdvancedExpanded)}
              aria-expanded={isAdvancedExpanded}
            >
              <span className="toggle-icon">{isAdvancedExpanded ? '▼' : '▶'}</span>
              <span className="toggle-text">Advanced Filters</span>
            </button>

            {isAdvancedExpanded && (
              <div className="advanced-content">
                <div className="advanced-grid">
                  <div className="settings-row">
                    <label htmlFor="measurement-type" className="settings-label-compact">
                      Measurement Type
                      <span className="settings-tooltip" title="Filter by the NTP protocol version used for measurement">?</span>
                    </label>
                    <select
                      id="measurement-type"
                      className="settings-select-compact"
                      value={measurementType}
                      onChange={(e) => setMeasurementType(e.target.value)}
                    >
                      {MEASUREMENT_TYPES.map(type => (
                        <option key={type.value} value={type.value}>{type.label}</option>
                      ))}
                    </select>
                    {showNtpv5Draft && (
                      <>
                        <label htmlFor="ntpv5-draft-filter" className="settings-label-compact">
                          NTPv5 Draft
                          <span className="settings-tooltip" title="Specify which NTPv5 draft name to use">?</span>
                        </label>
                        <select
                          id="ntpv5-draft-filter"
                          className="settings-select-compact"
                          value={isCustomDraft ? 'custom' : currentDraft}
                          onChange={(e) => {
                            if (e.target.value === 'custom') {
                              setShowCustomDraftInput(true);
                              setNtpv5DraftFilter('custom');
                            } else {
                              setShowCustomDraftInput(false);
                              setNtpv5DraftFilter(e.target.value);
                              setCustomDraftFilter('');
                            }
                          }}
                        >
                          {NTPV5_DRAFTS.map(draft => (
                            <option key={draft.value} value={draft.value}>{draft.label}</option>
                          ))}
                        </select>
                        {shouldShowCustomInput && (
                          <>
                            <label htmlFor="custom-draft-filter" className="settings-label-compact">
                              Custom Draft Name
                              <span className="settings-tooltip" title="Enter a custom NTPv5 draft name (max 50 characters)">?</span>
                            </label>
                            <input
                              id="custom-draft-filter"
                              type="text"
                              className="settings-input-compact"
                              value={isCustomDraft ? currentDraft : customDraftFilter}
                              onChange={(e) => {
                                const value = e.target.value.slice(0, 50);
                                setCustomDraftFilter(value.trim());
                                setNtpv5DraftFilter(value.trim() || 'draft-ietf-ntp-ntpv5-06');
                                if (value.trim()) {
                                  setShowCustomDraftInput(true);
                                }
                              }}
                              placeholder="Enter custom draft name"
                              maxLength={50}
                            />
                          </>
                        )}
                      </>
                    )}
                  </div>

                  <div className="settings-row">
                    <label htmlFor="reference-id-filter" className="settings-label-compact">
                      Reference ID
                    </label>
                    <input
                      id="reference-id-filter"
                      type="text"
                      className="settings-input-compact"
                      value={referenceIdFilter}
                      onChange={(e) => setReferenceIdFilter(e.target.value)}
                      placeholder="e.g., GOOG, GPS, IP address"
                    />
                  </div>

                  <div className="settings-row">
                    <label htmlFor="ip-version" className="settings-label-compact">
                      IP Version
                      <span className="settings-tooltip" title="Filter by IPv4 or IPv6">?</span>
                    </label>
                    <select
                      id="ip-version"
                      className="settings-select-compact"
                      value={ipVersionFilter}
                      onChange={(e) => setIpVersionFilter(e.target.value)}
                    >
                      <option value="">Any</option>
                      <option value="4">IPv4</option>
                      <option value="6">IPv6</option>
                    </select>
                  </div>

                  <div className="settings-row">
                    <label htmlFor="asn-filter" className="settings-label-compact">
                      ASN
                    </label>
                    <input
                      id="asn-filter"
                      type="text"
                      className="settings-input-compact"
                      value={asnFilter}
                      onChange={(e) => setAsnFilter(e.target.value)}
                      placeholder="e.g., AS15169"
                    />
                  </div>

                  <div className="settings-row">
                    <label htmlFor="country-filter" className="settings-label-compact">
                      Country
                      <span className="settings-tooltip" title="2 letter country code">?</span>
                    </label>
                    <input
                      id="country-filter"
                      type="text"
                      className="settings-input-compact"
                      value={countryFilter}
                      onChange={(e) => setCountryFilter(e.target.value.toUpperCase())}
                      placeholder="e.g., NL, US"
                      maxLength={2}
                    />
                  </div>

                  <div className="settings-row">
                    <label htmlFor="stratum-filter" className="settings-label-compact">
                      Stratum
                      <span className="settings-tooltip" title="Time server hierarchy level">?</span>
                    </label>
                    <select
                      id="stratum-filter"
                      className="settings-select-compact"
                      value={stratumFilter}
                      onChange={(e) => setStratumFilter(e.target.value)}
                    >
                      <option value="">Any</option>
                      <option value="1">Stratum 1</option>
                      <option value="2">Stratum 2</option>
                      <option value="3">Stratum 3</option>
                      <option value="4">Stratum 4+</option>
                    </select>
                  </div>

                  <div className="settings-row">
                    <label htmlFor="nts-filter" className="settings-label-compact">
                      NTS Support
                      <span className="settings-tooltip" title="Network Time Security support">?</span>
                    </label>
                    <select
                      id="nts-filter"
                      className="settings-select-compact"
                      value={ntsFilter}
                      onChange={(e) => setNtsFilter(e.target.value)}
                    >
                      <option value="">Any</option>
                      <option value="yes">Supported</option>
                      <option value="no">Not Supported</option>
                    </select>
                  </div>

                  <div className="settings-row">
                    <label htmlFor="offset-min" className="settings-label-compact">
                      Offset Min (ms)
                      <span className="settings-tooltip" title="Minimum time offset">?</span>
                    </label>
                    <input
                      id="offset-min"
                      type="number"
                      className="settings-input-compact"
                      value={offsetMin}
                      onChange={(e) => setOffsetMin(e.target.value)}
                      placeholder="e.g., -100"
                      step="0.1"
                    />
                  </div>

                  <div className="settings-row">
                    <label htmlFor="offset-max" className="settings-label-compact">
                      Offset Max (ms)
                      <span className="settings-tooltip" title="Maximum time offset">?</span>
                    </label>
                    <input
                      id="offset-max"
                      type="number"
                      className="settings-input-compact"
                      value={offsetMax}
                      onChange={(e) => setOffsetMax(e.target.value)}
                      placeholder="e.g., 100"
                      step="0.1"
                    />
                  </div>

                  <div className="settings-row full-width">
                    <label className="settings-label-compact">
                      NTP Versions Supported
                    </label>
                    <div className="settings-checkbox-group-compact">
                      {NTP_VERSIONS.map(version => (
                        <label key={version.value} className="settings-checkbox-label-compact">
                          <input
                            type="checkbox"
                            className="settings-checkbox"
                            checked={versionFilter.includes(version.value)}
                            onChange={() => handleVersionToggle(version.value)}
                          />
                          <span>{version.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="settings-row full-width">
                    <label htmlFor="date-from" className="settings-label-compact">
                      Date Range
                      <span className="settings-tooltip" title="Filter measurements by date range">?</span>
                    </label>
                    <div className="date-range-wrapper">
                      <input
                        id="date-from"
                        type="date"
                        className="settings-input-compact"
                        value={dateFrom}
                        onChange={(e) => setDateFrom(e.target.value)}
                        max={formatDateForInput(new Date())}
                      />
                      <span className="date-separator">to</span>
                      {usePresent ? (
                        <span className="present-badge">Present</span>
                      ) : (
                        <input
                          id="date-to"
                          type="date"
                          className="settings-input-compact"
                          value={dateTo}
                          onChange={(e) => setDateTo(e.target.value)}
                          max={formatDateForInput(new Date())}
                          min={dateFrom || undefined}
                        />
                      )}
                      <label className="present-checkbox-label">
                        <input
                          type="checkbox"
                          checked={usePresent}
                          onChange={(e) => setUsePresent(e.target.checked)}
                        />
                        <span>Present</span>
                      </label>
                    </div>
                  </div>

                  <div className="settings-row full-width">
                    <div className="reset-button-wrapper">
                      <button
                        type="button"
                        className="reset-filters-button"
                        onClick={clearFilters}
                      >
                        Reset Filters
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
              </div>
            </>
          ) : (
            <div className="main-search-row">
              <label htmlFor="id-search" className="main-search-label">
                Search by Measurement ID
              </label>
              <div className="main-search-input-wrapper">
                <input
                  id="id-search"
                  type="text"
                  className="main-search-input"
                  value={measurementIdQuery}
                  onChange={(e) => setMeasurementIdQuery(e.target.value)}
                  placeholder="e.g., dn32, or ip442"
                  onKeyDown={(e) => e.key === 'Enter' && !loading && !isSearchDisabled() && handleSearch()}
                />
                <button
                  className="search-submit-button"
                  onClick={handleSearch}
                  disabled={loading || isSearchDisabled()}
                >
                  {loading ? 'Searching...' : 'Search'}
                </button>
              </div>
            </div>
          )}
        </div>

        {hasSearched && (
          <div className="results-section">
            <div className="results-header">
              <div className="results-header-left">
                <h2>Results</h2>
                <span className="results-count">
                  {sortedResults.length.toLocaleString()} {sortedResults.length === 1 ? 'result' : 'results'}
                </span>
              </div>
              <div className="results-header-right">
                <div className="sort-controls">
                  <label htmlFor="sort-field">Sort by:</label>
                  <select
                    id="sort-field"
                    className="sort-select"
                    value={sortField}
                    onChange={(e) => setSortField(e.target.value as SortField)}
                  >
                    <option value="lastMeasured">Last Measured</option>
                    <option value="offset">Offset</option>
                    <option value="rtt">RTT</option>
                    <option value="stratum">Stratum</option>
                    <option value="server">Server</option>
                  </select>
                  <button
                    className="sort-order-button"
                    onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
                    title={`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`}
                  >
                    {sortOrder === 'asc' ? '↑' : '↓'}
                  </button>
                </div>
              </div>
            </div>

            {loading ? (
              <div className="loading-state">
                <div className="spinner"></div>
                <p>Searching measurements...</p>
              </div>
            ) : sortedResults.length === 0 ? (
              <div className="no-results">
                <p>No measurements found matching your criteria.</p>
                <p className="no-results-hint">Try adjusting your search filters.</p>
              </div>
            ) : (
              <>
                <div className="results-table-container">
                  <table className="results-table">
                    <thead>
                      <tr>
                        <th>Server</th>
                        <th>IP Address</th>
                        <th>ASN</th>
                        <th>Country</th>
                        <th>Offset (ms)</th>
                        <th>RTT (ms)</th>
                        <th>Stratum</th>
                        <th>Versions</th>
                        <th>NTS</th>
                        <th>Last Measured</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paginatedResults.map((result) => (
                        <tr key={result.id}>
                          <td className="server-cell">
                            <strong>{result.server}</strong>
                          </td>
                          <td className="ip-cell">{result.ip}</td>
                          <td className="asn-cell">{result.asn}</td>
                          <td className="country-cell">
                            <span className="country-flag">{result.country}</span>
                          </td>
                          <td className={`offset-cell ${Math.abs(result.offset) > 50 ? 'warning' : ''}`}>
                            {result.offset.toFixed(3)}
                          </td>
                          <td className="rtt-cell">{result.rtt.toFixed(2)}</td>
                          <td className="stratum-cell">
                            <span className="stratum-badge">S{result.stratum}</span>
                          </td>
                          <td className="versions-cell">
                            <div className="version-tags">
                              {result.supportedVersions.map(v => (
                                <span key={v} className="version-tag">{v}</span>
                              ))}
                            </div>
                          </td>
                          <td className="nts-cell">
                            {result.hasNTS ? (
                              <span className="nts-badge supported">✓ Yes</span>
                            ) : (
                              <span className="nts-badge not-supported">✗ No</span>
                            )}
                          </td>
                          <td className="date-cell">{result.lastMeasured}</td>
                          <td className="actions-cell">
                            <button
                              className="view-button"
                              onClick={() => {
                                console.log('View measurement:', result.measurementId);
                              }}
                            >
                              View
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {totalPages > 1 && (
                  <div className="pagination">
                    <button
                      className="pagination-button"
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                    >
                      ← Previous
                    </button>
                    <span className="pagination-info">
                      Page {currentPage} of {totalPages} 
                      <span className="pagination-detail">
                        (Showing {startIndex + 1}-{Math.min(endIndex, sortedResults.length)} of {sortedResults.length.toLocaleString()})
                      </span>
                    </span>
                    <button
                      className="pagination-button"
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                    >
                      Next →
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {!hasSearched && (
          <div className="search-info">
            <div className="info-card centered">
              <h3>🔍 Quick Search</h3>
              <p>Enter an IP address, domain name, or measurement ID in the search box above to find measurements instantly.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchTab;

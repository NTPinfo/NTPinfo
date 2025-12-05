import '../styles/ResultSummary.css'
import { NTPData, RIPEData, RipeStatus } from '../utils/types.ts'
import { useState, useEffect } from 'react'
import triangleGreen from '../assets/triangle-green-svgrepo-com.png'
import triangleRed from '../assets/triangle-red-svgrepo-com.png'
import linkIcon from '../assets/link-svgrepo-com.png'
import LoadingSpinner from './LoadingSpinner.tsx'
import { calculateStatus } from '../utils/calculateStatus.ts'
import { simplifyErrorMessage } from '../utils/simplifyErrorMessage.ts'

// Helper function to format numbers from scientific notation to readable format
function formatNumber(num: number | string | undefined): string {
    if (num === undefined || num === null) return 'N/A';
    const numValue = typeof num === 'string' ? parseFloat(num) : num;
    if (isNaN(numValue)) return 'N/A';
    
    // Check if the original string was in scientific notation or if the number is very small/large
    const originalStr = typeof num === 'string' ? num : numValue.toString();
    const isScientific = originalStr.includes('e') || originalStr.includes('E');
    
    if (isScientific || Math.abs(numValue) < 0.0001 || Math.abs(numValue) >= 1000000) {
        // Convert scientific notation to fixed decimal format
        // For very small numbers, show enough precision to be readable
        if (Math.abs(numValue) < 0.0001) {
            const formatted = numValue.toFixed(10);
            return formatted.replace(/\.?0+$/, '') || '0';
        } else {
            const formatted = numValue.toFixed(5);
            return formatted.replace(/\.?0+$/, '') || '0';
        }
    }
    
    // For regular numbers, return as string (remove trailing zeros if decimal)
    return numValue.toString().replace(/\.?0+$/, '');
}

// Helper function to format root delay and root dispersion with max 5 decimals
function formatRootValue(value: number | string | undefined): string {
    if (value === undefined || value === null) return 'N/A';
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(numValue)) return 'N/A';
    
    // Check if the original string was in scientific notation
    const originalStr = typeof value === 'string' ? value : numValue.toString();
    const isScientific = originalStr.includes('e') || originalStr.includes('E');
    
    if (isScientific || Math.abs(numValue) < 0.0001) {
        // For very small numbers in scientific notation, convert to readable format
        // Show up to 5 decimal places, but allow more for very small numbers
        if (Math.abs(numValue) < 0.0001) {
            const formatted = numValue.toFixed(10);
            return formatted.replace(/\.?0+$/, '') || '0';
        } else {
            const formatted = numValue.toFixed(6);
            return formatted.replace(/\.?0+$/, '') || '0';
        }
    }
    
    // Limit to 5 decimal places for regular numbers
    const formatted = numValue.toFixed(6);
    return formatted.replace(/\.?0+$/, '') || '0';
}


function ResultSummary({data, ripeData, ripeErr, ripeStatus, httpStatus, err, errMessage, measurementId,
        allNtpMeasurements, allRipeMeasurements, currentNtpIndex, currentRipeIndex, onNtpIndexChange, onRipeIndexChange,
        expectedIpCount, isLoading, ripeId, ripeErrorMessage} :
    {data : NTPData | null, ripeData: RIPEData | null, ripeErr: Error | null, ripeStatus: RipeStatus | null, 
        httpStatus: number, err: Error | null, errMessage: string | null, measurementId: string | null,
        allNtpMeasurements: NTPData[] | null, allRipeMeasurements: RIPEData[] | null,
        currentNtpIndex: number, currentRipeIndex: number,
        onNtpIndexChange: (index: number) => void, onRipeIndexChange: (index: number) => void,
        expectedIpCount?: number, isLoading?: boolean, ripeId?: string | null, ripeErrorMessage?: string | null}) {

    const [serverStatus, setServerStatus] = useState<string | null>(null)
    const [statusMessage, setStatusMessage] = useState<string | null>("")   
    
    useEffect(() => {
    if (data == null) {
        setStatusMessage(errMessage || err?.message || null)
        }
    }, [data, errMessage, err])
    
    useEffect(() => {
        if((ripeStatus === "complete") && ripeData && data){
            setServerStatus(calculateStatus(data, ripeData))
        }
        else if (ripeErr) {
            setServerStatus(null)
        }
        else
            setServerStatus(null)
    }, [data, ripeData, ripeErr, ripeStatus])

    // If data is null but we have error info, show error banner but continue rendering
    const hasError = data == null && (err || errMessage);
    const errorDisplay = hasError ? (
        <div className="error-banner" style={{
            backgroundColor: '#fee',
            border: '2px solid #f88',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '20px',
            color: '#c33'
        }}>
            <h3 style={{ margin: '0 0 8px 0', fontSize: '18px' }}>⚠️ Measurement Error</h3>
            <p style={{ margin: 0, fontSize: '14px' }}>
                {simplifyErrorMessage(errMessage || err?.message || statusMessage) || errMessage || err?.message || statusMessage || 'An error occurred during measurement'}
            </p>
            {httpStatus && httpStatus !== 200 && (
                <p style={{ margin: '8px 0 0 0', fontSize: '12px', opacity: 0.8 }}>
                    HTTP Status: {httpStatus}
                </p>
            )}
        </div>
    ) : null;

    // If we have no data and no other results to show, display error-only view
    if (data == null && !ripeData && !errorDisplay) {
        if (err && errMessage) {
            return <h2 id="not-found">Error {httpStatus}: {statusMessage}</h2>
        }
        return null;
    }



    // Compares the currently displayed NTP measurement (data) with the currently displayed RIPE measurement (ripeData)
    function getMetricIcons(ntpValue: number | undefined, ripeValue: number | undefined, lowerIsBetter = true) {
        if (ntpValue === undefined || ripeValue === undefined) return [null, null];
        if (ntpValue === ripeValue) return [triangleGreen, triangleGreen];
        if (lowerIsBetter) {
            return ntpValue < ripeValue ? [triangleGreen, triangleRed] : [triangleRed, triangleGreen];
        } else {
            return ntpValue > ripeValue ? [triangleGreen, triangleRed] : [triangleRed, triangleGreen];
        }
    }

    // Extract values from the currently displayed measurements (data = current NTP, ripeData = current RIPE)
    const ntpOffset = data?.offset !== undefined ? data.offset : undefined;
    const ripeOffset = ripeData?.measurementData.offset !== undefined ? ripeData.measurementData.offset : undefined;
    const ntpRTT = data?.RTT !== undefined ? data.RTT : undefined;
    const ripeRTT = ripeData?.measurementData.RTT !== undefined ? ripeData.measurementData.RTT : undefined;

    // Check if RIPE measurement failed (RTT = -1000 is a hardcoded failure value)
    const isRipeMeasurementFailed = ripeRTT === -1000;
    
    // Check if NTP measurement failed - check multiple indicators:
    // 1. data is null (no measurement data)
    // 2. data.hasError is true (explicit error flag)
    // 3. data.errorMessage exists (error message present)
    // 4. hasError is true (global error state when data is null)
    const isNtpMeasurementFailed = data == null || data?.hasError === true || (data?.errorMessage != null && data.errorMessage !== '') || hasError;
    
    // Only show comparison arrows if both measurements are valid
    const bothMeasurementsValid = !isNtpMeasurementFailed && !isRipeMeasurementFailed;

    // Compare the currently displayed NTP measurement with the currently displayed RIPE measurement
    // Only generate icons if both measurements are valid
    const [offsetIconNTP, offsetIconRIPE] = bothMeasurementsValid ? getMetricIcons(
        ntpOffset !== undefined ? Math.abs(ntpOffset) : undefined,
        ripeOffset !== undefined ? Math.abs(ripeOffset) : undefined,
        true
    ) : [null, null];
    const [rttIconNTP, rttIconRIPE] = bothMeasurementsValid ? getMetricIcons(ntpRTT, ripeRTT, true) : [null, null];

    // For precision, compare numeric values (handle both number and string formats)
    const ntpPrecisionNum = data?.precision !== undefined 
        ? (typeof data.precision === 'number' ? data.precision : parseFloat(String(data.precision)))
        : undefined;
    const ripePrecisionNum = ripeData?.measurementData.precision !== undefined 
        ? (typeof ripeData.measurementData.precision === 'number' 
            ? ripeData.measurementData.precision 
            : parseFloat(String(ripeData.measurementData.precision)))
        : undefined;
    const [precisionIconNTP, precisionIconRIPE] = bothMeasurementsValid ? getMetricIcons(
        !isNaN(ntpPrecisionNum!) ? ntpPrecisionNum : undefined,
        !isNaN(ripePrecisionNum!) ? ripePrecisionNum : undefined,
        true
    ) : [null, null];

    const ntpRootDispersion = data?.root_dispersion !== undefined ? data.root_dispersion : undefined;
    const ripeRootDispersion = ripeData?.measurementData.root_dispersion !== undefined ? ripeData.measurementData.root_dispersion : undefined;
    const [rootDispIconNTP, rootDispIconRIPE] = bothMeasurementsValid ? getMetricIcons(ntpRootDispersion, ripeRootDispersion, true) : [null, null];

    return (
        <>
            <div className="results-section">
                {errorDisplay}
                <div className="status-line">
                    <span className="status-label">STATUS:&nbsp;</span>
                    <span className={`status-value ${serverStatus?.toLowerCase()}`}>{serverStatus || (hasError ? 'ERROR' : 'UNKNOWN')}</span>
                    {ripeStatus === "complete" && (
                    <div className="tooltip-container">
                        <span className="tooltip-icon">?</span>
                        {serverStatus === "PASSING" &&
                            <div className="tooltip-text">
                            The status of the NTP server, calculated with the offset
                            of our measurement and the offset of the RIPE Probe.<br/>
                            Both offsets are less than {import.meta.env.VITE_STATUS_THRESHOLD} ms.
                            </div>
                        }
                        {serverStatus === "CAUTION" &&
                            <div className="tooltip-text">
                            The status of the NTP server, calculated with the offset
                            of our measurement and the offset of the RIPE Probe.<br/>
                            One of the offsets is more than {import.meta.env.VITE_STATUS_THRESHOLD} ms.
                            </div>
                        }
                        {serverStatus === "FAILING" &&
                            <div className="tooltip-text">
                            The status of the NTP server, calculated with the offset
                            of our measurement and the offset of the RIPE Probe.<br/>
                            Both offsets are more than {import.meta.env.VITE_STATUS_THRESHOLD} ms.
                            </div>
                        }
                        {serverStatus === null &&
                            <div className="tooltip-text">
                            The status of the NTP server, calculated with the offset
                            of our measurement and the offset of the RIPE Probe.<br/>
                            There was an error in one of the measurements.
                            </div>
                        }
                    </div>)}
                </div>

                <div className="result-boxes-container">
                    <div className="result-and-title">
                    <div className="res-label"> 
                        Results from our <a href="https://time.nl" target="_blank">ntp.time.nl</a> synced server:
                            <div className="tooltip-container">
                            <span className="tooltip-icon">?</span>
                            <div className="tooltip-text">
                               Our NTP Client is based in the Netherlands.
                            </div>
                            </div>
                        </div>
                        {data?.hasError ? (
                            <div className="result-box" id="main-details">
                                <div className="metric"><span title='The difference between the time reported by the like an NTP server and your local clock'>Offset</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                                <div className="metric"><span title='The total time taken for a request to travel from the client to the server and back.'>Round-trip time</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                                <div className="metric"><span title='The variability in delay times between successive NTP messages, calculated as std. dev. of offsets'>Jitter</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                                <div className="metric" style={{height: '22.8px'}}><span title='The smallest time unit that the NTP server can measure or represent'>Precision</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                                <div className="metric"><span title='A hierarchical level number indicating the distance from the reference clock'>Stratum</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                                <div className="metric"><span title='The IP address of the NTP server'>IP address</span><span style={{ color: '#dc2626', fontWeight: 'bold' }}>{data.ip || 'Unknown'}</span></div>
                                <div className="metric"><span>Vantage point IP</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                                <div className="metric"><span>Country</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                                <div className="metric"><span>Reference ID</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                                <div className="metric"><span title='The total round-trip delay to the primary reference source'>Root delay</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                                <div className="metric"><span title='The poll interval used during the measurement'>Poll interval</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                                <div className="metric"><span title='An estimate of the maximum error due to clock frequency stability'>Root dispersion</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                                <div className="metric"><span title='The ASN of the server'>ASN</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                                <div className="metric"><span title='The NTP version used for this measurement'>NTP Version</span><span style={{ color: '#dc2626', fontWeight: 'bold' }}>N/A</span></div>
                                <div className="metric"><span>Measurement ID</span><span>{measurementId ?? 'N/A'}</span></div>
                                <div className="metric" style={{ marginTop: '8px', padding: '6px 8px', backgroundColor: '#fef2f2', borderRadius: '4px', border: '1px solid #fca5a5', whiteSpace: 'normal' }}>
                                    <span style={{ color: '#dc2626', fontWeight: 'bold' }}>Error</span>
                                    <span style={{ color: '#dc2626', fontSize: '0.9rem', wordBreak: 'break-word', overflowWrap: 'break-word', maxWidth: 'calc(100% - 2rem)' }}>{simplifyErrorMessage(data.errorMessage) || 'Measurement failed'}</span>
                                </div>
                            </div>
                        ) : data ? (
                        <div className="result-box" id="main-details">
                            <div className="metric"><span title='The difference between the time reported by the like an NTP server and your local clock'>Offset</span><span>{data?.offset !== undefined ? `${(data.offset).toFixed(3)} ms` : 'N/A'} {offsetIconNTP && <img src={offsetIconNTP} alt="offset performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                            <div className="metric"><span title='The total time taken for a request to travel from the client to the server and back.'>Round-trip time</span><span>{data?.RTT !== undefined ? `${(data.RTT).toFixed(3)} ms` : 'N/A'} {rttIconNTP && <img src={rttIconNTP} alt="rtt performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                            <div className="metric"><span title={`The variability in delay times between successive NTP messages, calculated as std. dev. of ${data?.nr_measurements_jitter} offsets`}>Jitter</span><span>{data?.jitter ? `${(data.jitter).toFixed(3)} ms` : 'N/A'}</span></div>
                            <div className="metric" style = {{height: '22.8px'}}><span title='The smallest time unit that the NTP server can measure or represent'>Precision</span><span>{data?.precision !== undefined ? (typeof data.precision === 'number' ? <>2<sup>{data.precision}</sup></> : formatNumber(data.precision)) : 'N/A'} {precisionIconNTP && <img src={precisionIconNTP} alt="precision performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                            <div className="metric"><span title='A hierarchical level number indicating the distance from the reference clock'>Stratum</span><span>{data?.stratum !== undefined ? data.stratum : 'N/A'}</span></div>
                            <div className="metric"><span title='The IP address of the NTP server'>IP address</span><span>{data?.ip ? data.ip : 'N/A'}</span></div>
                            <div className="metric"><span>Vantage point IP</span><span>{data?.vantage_point_ip}</span></div>
                            <div className="metric"><span>Country</span><span>{data?.country_code ? data.country_code : 'N/A'}</span></div>
                            <div className="metric"><span>Reference ID</span><span>{data?.ref_id}</span></div>
                            <div className="metric"><span title='The total round-trip delay to the primary reference source'>Root delay</span><span>{data?.root_delay !== undefined ? formatRootValue(data.root_delay) : 'N/A'}</span></div>
                            <div className="metric"><span title='The poll interval used by the probe during the measurement'>Poll interval</span><span>{data?.poll !== undefined ? `${Math.pow(2, data.poll)} s` : 'N/A'}</span></div>
                            <div className="metric"><span title='An estimate of the maximum error due to clock frequency stability'>Root dispersion</span><span>{data?.root_dispersion !== undefined ? `${formatRootValue(data.root_dispersion)} s` : 'N/A'} {rootDispIconNTP && <img src={rootDispIconNTP} alt="root dispersion performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                            <div className="metric"><span title='The ASN of the server'>ASN</span><span>{data?.asn_ntp_server !== undefined ? data.asn_ntp_server : "N/A"}</span></div>
                            <div className="metric"><span title='The NTP version used for this measurement'>NTP Version</span><span>{data?.response_version || 'N/A'}</span></div>
                            <div className="metric"><span>Measurement ID</span><span>{measurementId ?? 'N/A'}</span></div>
                        </div>
                        ) : (isLoading && !allNtpMeasurements && !expectedIpCount && !err && !errMessage) ? null : (
                        <div className="result-box" id="main-details">
                            <div className="metric"><span title='The difference between the time reported by the like an NTP server and your local clock'>Offset</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                            <div className="metric"><span title='The total time taken for a request to travel from the client to the server and back.'>Round-trip time</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                            <div className="metric"><span title={`The variability in delay times between successive NTP messages, calculated as std. dev. of offsets`}>Jitter</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                            <div className="metric" style = {{height: '22.8px'}}><span title='The smallest time unit that the NTP server can measure or represent'>Precision</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                            <div className="metric"><span title='A hierarchical level number indicating the distance from the reference clock'>Stratum</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                            <div className="metric"><span title='The IP address of the NTP server'>IP address</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                            <div className="metric"><span>Vantage point IP</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                            <div className="metric"><span>Country</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                            <div className="metric"><span>Reference ID</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                            <div className="metric"><span title='The total round-trip delay to the primary reference source'>Root delay</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                            <div className="metric"><span title='The poll interval used by the probe during the measurement'>Poll interval</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                            <div className="metric"><span title='An estimate of the maximum error due to clock frequency stability'>Root dispersion</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                            <div className="metric"><span title='The ASN of the server'>ASN</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                            <div className="metric"><span title='The NTP version used for this measurement'>NTP Version</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                            <div className="metric"><span>Measurement ID</span><span>{measurementId ?? 'N/A'}</span></div>
                        </div>
                        )}
                        {((allNtpMeasurements && allNtpMeasurements.length > 1) || 
                          (expectedIpCount && expectedIpCount > 1 && (allNtpMeasurements?.length || 0) >= 1) ||
                          (isLoading && allNtpMeasurements && allNtpMeasurements.length >= 1)) && (
                            <div className="measurement-navigation">
                                <button 
                                    className="nav-button nav-button-prev" 
                                    onClick={() => onNtpIndexChange(Math.max(0, currentNtpIndex - 1))}
                                    disabled={currentNtpIndex === 0}
                                    aria-label="Previous NTP measurement"
                                    title="Previous measurement"
                                >
                                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M10 12L6 8L10 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                    </svg>
                                </button>
                                <span className="nav-counter">
                                    {currentNtpIndex + 1} / {expectedIpCount && expectedIpCount > (allNtpMeasurements?.length || 0) 
                                        ? expectedIpCount 
                                        : (allNtpMeasurements?.length || 1)}
                                    {isLoading && expectedIpCount && expectedIpCount > (allNtpMeasurements?.length || 0) && ' (loading...)'}
                                </span>
                                <button 
                                    className="nav-button nav-button-next" 
                                    onClick={() => {
                                        const maxIndex = expectedIpCount && expectedIpCount > (allNtpMeasurements?.length || 0)
                                            ? expectedIpCount - 1
                                            : (allNtpMeasurements?.length || 1) - 1;
                                        onNtpIndexChange(Math.min(maxIndex, currentNtpIndex + 1));
                                    }}
                                    disabled={expectedIpCount 
                                        ? currentNtpIndex >= expectedIpCount - 1 
                                        : currentNtpIndex >= (allNtpMeasurements?.length || 1) - 1}
                                    aria-label="Next NTP measurement"
                                    title="Next measurement"
                                >
                                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M6 12L10 8L6 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                    </svg>
                                </button>
                            </div>
                        )}
                    </div>
                    <div className="result-and-title" id="ripe-result">
                    <div className="res-label">
                        Results from <a href="https://atlas.ripe.net" target="_blank">RIPE Atlas probes</a> (close to your location):
                        <div className="tooltip-container">
                        {((ripeStatus === "timeout" || (ripeStatus === "error" && !ripeData) || ripeData?.measurementData.RTT === -1000.000) && <span className="tooltip-icon fail">!</span>) ||
                        (<span className="tooltip-icon success">?</span>)}
                            <div className="tooltip-text">
                                {(ripeStatus === "timeout" && <span>RIPE Measurement timed out. <br /> </span>) ||
                                (ripeStatus === "error" && !ripeData && <span>RIPE Measurement failed. <br /></span>) || 
                                (ripeData?.measurementData.RTT === -1000.000 && <span> Probe failed to respond. <br /></span>)}
                                RIPE Atlas tries to choose 3 probes near the user to perform more accurate measurements. This can take longer.
                            </div>
                        </div>
                    </div>

                        { (ripeId === null && ripeErrorMessage) ? (
                    <div className="result-box" id="ripe-details">
                        <div className="metric"><span title='The difference between the time reported by the like an NTP server and your local clock'>Offset</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                        <div className="metric"><span title='The total time taken for a request to travel from the client to the server and back.'>Round-trip time</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                        <div className="metric"><span title='The variability in delay times between successive NTP messages, calculated as std. dev. of offsets'>Jitter</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                        <div className="metric"><span title='The smallest time unit that the NTP server can measure or represent'>Precision</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                        <div className="metric"><span title='A hierarchical level number indicating the distance from the reference clock'>Stratum</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                        <div className="metric"><span title='The IP address of the NTP server'>IP address</span><span>{data?.ip || 'N/A'}</span></div>
                        <div className="metric"><span>Vantage point IP</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                        <div className="metric"><span>Country</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                        <div className="metric"><span>Reference ID</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                        <div className="metric"><span title='The total round-trip delay to the primary reference source'>Root delay</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                        <div className="metric"><span title='The poll interval used by the probe during the measurement'>Poll interval</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                        <div className="metric"><span title='An estimate of the maximum error due to clock frequency stability'>Root dispersion</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                        <div className="metric"><span title='The ASN of the server'>ASN</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                        <div className="metric"><span title='The NTP version used for this measurement'>NTP Version</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                        <div className="metric"><span>Measurement ID</span><span style={{ color: '#c33', fontWeight: 'bold' }}>N/A</span></div>
                        <div className="metric" style={{ marginTop: '8px', padding: '6px 8px', backgroundColor: '#fef2f2', borderRadius: '4px', border: '1px solid #fca5a5', whiteSpace: 'normal' }}>
                            <span style={{ color: '#dc2626', fontWeight: 'bold' }}>Error</span>
                            <span style={{ color: '#dc2626', fontSize: '0.9rem', wordBreak: 'break-word', overflowWrap: 'break-word', maxWidth: 'calc(100% - 2rem)' }}>{simplifyErrorMessage(ripeErrorMessage) || 'RIPE measurement failed'}</span>
                        </div>
                    </div>
                        ) : ((ripeStatus === "complete" || ripeStatus === "timeout") &&
                    (
                    <div className="result-box" id="ripe-details">
                        <div className="metric"><span title='The difference between the time reported by the like an NTP server and your local clock'>Offset</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.offset !== undefined ? `${(ripeData.measurementData.offset).toFixed(3)} ms` : 'N/A'} {!isRipeMeasurementFailed && offsetIconRIPE && <img src={offsetIconRIPE} alt="offset performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                        <div className="metric"><span title='The total time taken for a request to travel from the client to the server and back.'>Round-trip time</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.RTT !== undefined ? `${(ripeData.measurementData.RTT).toFixed(3)} ms` : 'N/A'} {!isRipeMeasurementFailed && rttIconRIPE && <img src={rttIconRIPE} alt="rtt performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                        <div className="metric"><span title='The variability in delay times between successive NTP messages, calculated as std. dev. of offsets'>Jitter</span><span>{'N/A'}</span></div>
                        <div className="metric"><span title='The smallest time unit that the NTP server can measure or represent'>Precision</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.precision !== undefined ? formatNumber(ripeData.measurementData.precision) : 'N/A'} {!isRipeMeasurementFailed && precisionIconRIPE && <img src={precisionIconRIPE} alt="precision performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                        <div className="metric"><span title='A hierarchical level number indicating the distance from the reference clock'>Stratum</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.stratum !== undefined ? ripeData.measurementData.stratum : 'N/A'}</span></div>
                        <div className="metric"><span title='The IP address of the NTP server'>IP address</span><span>{ripeData?.measurementData.ip}</span></div>
                        <div className="metric"><span>Vantage point IP</span><span>{ripeData?.measurementData.vantage_point_ip}</span></div>
                        <div className="metric"><span>Country</span><span>{ripeData?.measurementData.country_code ? ripeData.measurementData.country_code : 'N/A'}</span></div>
                        <div className="metric"><span>Reference ID</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.ref_id ? ripeData.measurementData.ref_id : 'N/A'}</span></div>
                        <div className="metric"><span title='The total round-trip delay to the primary reference source'>Root delay</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.root_delay !== undefined ? formatRootValue(ripeData.measurementData.root_delay) : 'N/A'}</span></div>
                        <div className="metric"><span title='The poll interval used by the probe during the measurement'>Poll interval</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.poll !== undefined ? `${ripeData.measurementData.poll} s` : 'N/A'}</span></div>
                        <div className="metric"><span title='An estimate of the maximum error due to clock frequency stability'>Root dispersion</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.root_dispersion !== undefined ? `${formatRootValue(ripeData.measurementData.root_dispersion)} s` : 'N/A'} {!isRipeMeasurementFailed && rootDispIconRIPE && <img src={rootDispIconRIPE} alt="root dispersion performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                        <div className="metric"><span title='The ASN of the server'>ASN</span><span>{ripeData?.measurementData.asn_ntp_server !== undefined ? ripeData.measurementData.asn_ntp_server : 'N/A' }</span></div>
                        <div className="metric"><span title='The NTP version used for this measurement'>NTP Version</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.ntp_version !== undefined && ripeData.measurementData.ntp_version !== -1 ? ripeData.measurementData.ntp_version : 'N/A'}</span></div>
                        <div className="metric"><span>Measurement ID</span><span>
                            {ripeData?.measurement_id ? (
                                <a
                                    href={`https://atlas.ripe.net/measurements/${ripeData.measurement_id}/`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="measurement-link"
                                    style={{textDecoration:'underline'}}
                                >
                                    {ripeData.measurement_id}
                                    <img src={linkIcon} alt="external link" style={{width:'14px',verticalAlign:'middle',marginLeft:'4px',transform:'translateY(-1px)'}} />
                                </a>
                            ) : 'N/A'}
                        </span></div>
                    </div>)) ||
                    ((ripeStatus === "pending" || ripeStatus === "partial_results") && (
                        <div className="loading-container">
                            <p className="ripe-loading-text">Running RIPE measurements. This may take a while.</p>
                            <LoadingSpinner size="medium"/>
                        </div>
                    )) ||
                    (ripeStatus === "error" && !ripeData && (<p className="ripe-err">RIPE measurement failed</p>)) ||
                    (ripeStatus === "error" && ripeData && (
                    <div className="result-box" id="ripe-details">
                        <div className="metric"><span title='The difference between the time reported by the like an NTP server and your local clock'>Offset</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.offset !== undefined ? `${(ripeData.measurementData.offset).toFixed(3)} ms` : 'N/A'} {!isRipeMeasurementFailed && offsetIconRIPE && <img src={offsetIconRIPE} alt="offset performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                        <div className="metric"><span title='The total time taken for a request to travel from the client to the server and back.'>Round-trip time</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.RTT !== undefined ? `${(ripeData.measurementData.RTT).toFixed(3)} ms` : 'N/A'} {!isRipeMeasurementFailed && rttIconRIPE && <img src={rttIconRIPE} alt="rtt performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                        <div className="metric"><span title='The variability in delay times between successive NTP messages, calculated as std. dev. of offsets'>Jitter</span><span>{'N/A'}</span></div>
                        <div className="metric"><span title='The smallest time unit that the NTP server can measure or represent'>Precision</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.precision !== undefined ? formatNumber(ripeData.measurementData.precision) : 'N/A'} {!isRipeMeasurementFailed && precisionIconRIPE && <img src={precisionIconRIPE} alt="precision performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                        <div className="metric"><span title='A hierarchical level number indicating the distance from the reference clock'>Stratum</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.stratum !== undefined ? ripeData.measurementData.stratum : 'N/A'}</span></div>
                        <div className="metric"><span title='The IP address of the NTP server'>IP address</span><span>{ripeData?.measurementData.ip}</span></div>
                        <div className="metric"><span>Vantage point IP</span><span>{ripeData?.measurementData.vantage_point_ip}</span></div>
                        <div className="metric"><span>Country</span><span>{ripeData?.measurementData.country_code ? ripeData.measurementData.country_code : 'N/A'}</span></div>
                        <div className="metric"><span>Reference ID</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.ref_id ? ripeData.measurementData.ref_id : 'N/A'}</span></div>
                        <div className="metric"><span title='The total round-trip delay to the primary reference source'>Root delay</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.root_delay !== undefined ? formatRootValue(ripeData.measurementData.root_delay) : 'N/A'}</span></div>
                        <div className="metric"><span title='The poll interval used by the probe during the measurement'>Poll interval</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.poll !== undefined ? `${ripeData.measurementData.poll} s` : 'N/A'}</span></div>
                        <div className="metric"><span title='An estimate of the maximum error due to clock frequency stability'>Root dispersion</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.root_dispersion !== undefined ? `${formatRootValue(ripeData.measurementData.root_dispersion)} s` : 'N/A'} {!isRipeMeasurementFailed && rootDispIconRIPE && <img src={rootDispIconRIPE} alt="root dispersion performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                        <div className="metric"><span title='The ASN of the server'>ASN</span><span>{ripeData?.measurementData.asn_ntp_server !== undefined ? ripeData.measurementData.asn_ntp_server : 'N/A' }</span></div>
                        <div className="metric"><span title='The NTP version used for this measurement'>NTP Version</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.ntp_version !== undefined && ripeData.measurementData.ntp_version !== -1 ? ripeData.measurementData.ntp_version : 'N/A'}</span></div>
                        <div className="metric"><span>Measurement ID</span><span>
                            {ripeData?.measurement_id ? (
                                <a
                                    href={`https://atlas.ripe.net/measurements/${ripeData.measurement_id}/`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="measurement-link"
                                    style={{textDecoration:'underline'}}
                                >
                                    {ripeData.measurement_id}
                                    <img src={linkIcon} alt="external link" style={{width:'14px',verticalAlign:'middle',marginLeft:'4px',transform:'translateY(-1px)'}} />
                                </a>
                            ) : 'N/A'}
                        </span></div>
                    </div>))}
                        {allRipeMeasurements && allRipeMeasurements.length > 1 && (ripeStatus === "complete" || ripeStatus === "timeout" || (ripeStatus === "error" && ripeData)) && (
                            <div className="measurement-navigation">
                                <button 
                                    className="nav-button nav-button-prev" 
                                    onClick={() => onRipeIndexChange(Math.max(0, currentRipeIndex - 1))}
                                    disabled={currentRipeIndex === 0}
                                    aria-label="Previous RIPE measurement"
                                    title="Previous measurement"
                                >
                                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M10 12L6 8L10 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                    </svg>
                                </button>
                                <span className="nav-counter">
                                    {currentRipeIndex + 1} / {allRipeMeasurements.length}
                                </span>
                                <button 
                                    className="nav-button nav-button-next" 
                                    onClick={() => onRipeIndexChange(Math.min(allRipeMeasurements.length - 1, currentRipeIndex + 1))}
                                    disabled={currentRipeIndex === allRipeMeasurements.length - 1}
                                    aria-label="Next RIPE measurement"
                                    title="Next measurement"
                                >
                                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M6 12L10 8L6 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                    </svg>
                                </button>
                            </div>
                        )}
                    </div>

                </div>
            </div>
        </>
    )
}

export default ResultSummary;

import '../styles/ResultSummary.css'
import { NTPData, RIPEData, RipeStatus } from '../utils/types.ts'
import { useState, useEffect } from 'react'
import triangleGreen from '../assets/triangle-green-svgrepo-com.png'
import triangleRed from '../assets/triangle-red-svgrepo-com.png'
import linkIcon from '../assets/link-svgrepo-com.png'
import LoadingSpinner from './LoadingSpinner.tsx'
import { calculateStatus } from '../utils/calculateStatus.ts'


function ResultSummary({data, ripeData, ripeErr, ripeStatus, measurementId} :
    {data : NTPData | null, ripeData: RIPEData | null, ripeErr: Error | null, ripeStatus: RipeStatus | null, measurementId: string | null}) {

    const [serverStatus, setServerStatus] = useState<string | null>(null)

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

    // if (data == null)
    //     return <h2 id="not-found">{err && errMessage ? `Error ${httpStatus}: ${statusMessage}` : `Unknown error occurred`}</h2>



    // Helper to determine which icon to show for a metric
    function getMetricIcons(ntpValue: number | undefined, ripeValue: number | undefined, lowerIsBetter = true) {
        if (ntpValue === undefined || ripeValue === undefined) return [null, null];
        if (ntpValue === ripeValue) return [triangleGreen, triangleGreen];
        if (lowerIsBetter) {
            return ntpValue < ripeValue ? [triangleGreen, triangleRed] : [triangleRed, triangleGreen];
        } else {
            return ntpValue > ripeValue ? [triangleGreen, triangleRed] : [triangleRed, triangleGreen];
        }
    }

    const ntpOffset = data?.offset !== undefined ? data.offset : undefined;
    const ripeOffset = ripeData?.measurementData.offset !== undefined ? ripeData.measurementData.offset : undefined;
    const ntpRTT = data?.RTT !== undefined ? data.RTT : undefined;
    const ripeRTT = ripeData?.measurementData.RTT !== undefined ? ripeData.measurementData.RTT : undefined;

    // Check if RIPE measurement failed (RTT = -1000 is a hardcoded failure value)
    const isRipeMeasurementFailed = ripeRTT === -1000;

    const [offsetIconNTP, offsetIconRIPE] = getMetricIcons(
        ntpOffset !== undefined ? Math.abs(ntpOffset) : undefined,
        ripeOffset !== undefined ? Math.abs(ripeOffset) : undefined,
        true
    );
    const [rttIconNTP, rttIconRIPE] = getMetricIcons(ntpRTT, ripeRTT, true);


    const ntpPrecision = data?.precision !== undefined ? data.precision : undefined;
    const ripePrecision = ripeData?.measurementData.precision !== undefined ? ripeData.measurementData.precision : undefined;
    const [precisionIconNTP, precisionIconRIPE] = getMetricIcons(ntpPrecision, ripePrecision, true);

    const ntpRootDispersion = data?.root_dispersion !== undefined ? data.root_dispersion : undefined;
    const ripeRootDispersion = ripeData?.measurementData.root_dispersion !== undefined ? ripeData.measurementData.root_dispersion : undefined;
    const [rootDispIconNTP, rootDispIconRIPE] = getMetricIcons(ntpRootDispersion, ripeRootDispersion, true);

    return (
        <>
            <div className="results-section">
                <div className="status-line">
                    <span className="status-label">STATUS:&nbsp;</span>
                    <span className={`status-value ${serverStatus?.toLowerCase()}`}>{serverStatus}</span>
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
                        <div className="res-label">From our NTP Client (Netherlands)
                            <div className="tooltip-container">
                            <span className="tooltip-icon">?</span>
                            <div className="tooltip-text">
                               Our NTP Client is based in the Netherlands.
                            </div>
                            </div>
                        </div>
                        <div className="result-box" id="main-details">
                            <div className="metric"><span title='The difference between the time reported by the like an NTP server and your local clock'>Offset</span><span>{data?.offset !== undefined ? `${(data.offset).toFixed(3)} ms` : 'N/A'} {offsetIconNTP && <img src={offsetIconNTP} alt="offset performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                            <div className="metric"><span title='The total time taken for a request to travel from the client to the server and back.'>Round-trip time</span><span>{data?.RTT !== undefined ? `${(data.RTT).toFixed(3)} ms` : 'N/A'} {rttIconNTP && <img src={rttIconNTP} alt="rtt performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                            <div className="metric"><span title={`The variability in delay times between successive NTP messages, calculated as std. dev. of ${data?.nr_measurements_jitter} offsets`}>Jitter</span><span>{data?.jitter ? `${(data.jitter).toFixed(3)} ms` : 'N/A'}</span></div>
                            <div className="metric" style = {{height: '22.8px'}}><span title='The smallest time unit that the NTP server can measure or represent'>Precision</span><span>2<sup>{data?.precision !== undefined ? data.precision : 'N/A'}</sup> {precisionIconNTP && <img src={precisionIconNTP} alt="precision performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                            <div className="metric"><span title='A hierarchical level number indicating the distance from the reference clock'>Stratum</span><span>{data?.stratum !== undefined ? data.stratum : 'N/A'}</span></div>
                            <div className="metric"><span title='The IP address of the NTP server'>IP address</span><span>{data?.ip ? data.ip : 'N/A'}</span></div>
                            <div className="metric"><span>Vantage point IP</span><span>{data?.vantage_point_ip}</span></div>
                            <div className="metric"><span>Country</span><span>{data?.country_code ? data.country_code : 'N/A'}</span></div>
                            <div className="metric"><span>Reference ID</span><span>{data?.ref_id}</span></div>
                            <div className="metric"><span title='The total round-trip delay to the primary reference source'>Root delay</span><span>{data?.root_delay !== undefined ? data.root_delay : 'N/A'}</span></div>
                            <div className="metric"><span title='The poll interval used by the probe during the measurement'>Poll interval</span><span>{data?.poll !== undefined ? `${Math.pow(2, data.poll)} s` : 'N/A'}</span></div>
                            <div className="metric"><span title='An estimate of the maximum error due to clock frequency stability'>Root dispersion</span><span>{data?.root_dispersion !== undefined ? `${(data.root_dispersion).toFixed(10)} s` : 'N/A'} {rootDispIconNTP && <img src={rootDispIconNTP} alt="root dispersion performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                            <div className="metric"><span>ASN</span><span>{data?.asn_ntp_server !== undefined ? data.asn_ntp_server : "N/A"}</span></div>
                            <div className="metric"><span>Measurement ID</span><span>{measurementId ?? 'N/A'}</span></div>
                        </div>
                    </div>
                    <div className="result-and-title" id="ripe-result">
                        <div className="res-label">From the RIPE Atlas probe (Close to you)
                        <div className="tooltip-container">
                        {((ripeStatus === "timeout" || ripeStatus === "error"|| ripeData?.measurementData.RTT === -1000.000) && <span className="tooltip-icon fail">!</span>) ||
                        (<span className="tooltip-icon success">?</span>)}
                            <div className="tooltip-text">
                                {(ripeStatus === "timeout" && <span>RIPE Measurement timed out. <br /> </span>) ||
                                (ripeStatus === "error" && <span>RIPE Measurement failed. <br /></span>) || 
                                (ripeData?.measurementData.RTT === -1000.000 && <span> Probe failed to respond. <br /></span>)}
                                RIPE Atlas tries to choose a probe near the user to perform more accurate measurements. This can take longer.
                            </div>
                        </div>
                    </div>

                        { ((ripeStatus === "complete" || (ripeStatus === "timeout")) &&
                    (
                    <div className="result-box" id="ripe-details">
                        <div className="metric"><span title='The difference between the time reported by the like an NTP server and your local clock'>Offset</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.offset !== undefined ? `${(ripeData.measurementData.offset).toFixed(3)} ms` : 'N/A'} {!isRipeMeasurementFailed && offsetIconRIPE && <img src={offsetIconRIPE} alt="offset performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                        <div className="metric"><span title='The total time taken for a request to travel from the client to the server and back.'>Round-trip time</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.RTT !== undefined ? `${(ripeData.measurementData.RTT).toFixed(3)} ms` : 'N/A'} {!isRipeMeasurementFailed && rttIconRIPE && <img src={rttIconRIPE} alt="rtt performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                        <div className="metric"><span title='The variability in delay times between successive NTP messages, calculated as std. dev. of offsets'>Jitter</span><span>{'N/A'}</span></div>
                        <div className="metric"><span title='The smallest time unit that the NTP server can measure or represent'>Precision</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.precision !== undefined ? ripeData.measurementData.precision : 'N/A'} {!isRipeMeasurementFailed && precisionIconRIPE && <img src={precisionIconRIPE} alt="precision performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                        <div className="metric"><span title='A hierarchical level number indicating the distance from the reference clock'>Stratum</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.stratum !== undefined ? ripeData.measurementData.stratum : 'N/A'}</span></div>
                        <div className="metric"><span title='The IP address of the NTP server'>IP address</span><span>{ripeData?.measurementData.ip}</span></div>
                        <div className="metric"><span>Vantage point IP</span><span>{ripeData?.measurementData.vantage_point_ip}</span></div>
                        <div className="metric"><span>Country</span><span>{ripeData?.measurementData.country_code ? ripeData.measurementData.country_code : 'N/A'}</span></div>
                        <div className="metric"><span>Reference ID</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.ref_id ? ripeData.measurementData.ref_id : 'N/A'}</span></div>
                        <div className="metric"><span title='The total round-trip delay to the primary reference source'>Root delay</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.root_delay !== undefined ? ripeData.measurementData.root_delay : 'N/A'}</span></div>
                        <div className="metric"><span title='The poll interval used by the probe during the measurement'>Poll interval</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.poll !== undefined ? `${ripeData.measurementData.poll} s` : 'N/A'}</span></div>
                        <div className="metric"><span title='An estimate of the maximum error due to clock frequency stability'>Root dispersion</span><span>{!isRipeMeasurementFailed && ripeData?.measurementData.root_dispersion !== undefined ? `${(ripeData.measurementData.root_dispersion).toFixed(10)} s` : 'N/A'} {!isRipeMeasurementFailed && rootDispIconRIPE && <img src={rootDispIconRIPE} alt="root dispersion performance" style={{width:'14px',verticalAlign:'middle'}}/>}</span></div>
                        <div className="metric"><span>ASN</span><span>{ripeData?.measurementData.asn_ntp_server !== undefined ? ripeData.measurementData.asn_ntp_server : 'N/A' }</span></div>
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
                    (ripeStatus === "error" && (<p className="ripe-err">RIPE measurement failed</p>))}
                    </div>

                </div>
            </div>
        </>
    )
}

export default ResultSummary;

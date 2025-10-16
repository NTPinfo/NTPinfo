import { CheckCircle2, XCircle, AlertTriangle } from "lucide-react"
import { useState } from "react"
import { NTPVersionsData } from "../utils/types"
import "../styles/NtpVersions.css"

type VersionStatus = "supported" | "not-supported" | "partial" | "not-measured"

const statusConfig = {
  supported: {
    icon: CheckCircle2,
    color: "border-green-600 bg-green-50 text-green-700",
    label: "Supported",
    iconColor: "text-green-600",
  },
  "not-supported": {
    icon: XCircle,
    color: "border-red-600 bg-red-50 text-red-700",
    label: "Not Supported",
    iconColor: "text-red-600",
  },
  partial: {
    icon: AlertTriangle,
    color: "border-amber-600 bg-amber-50 text-amber-700",
    label: "Partial Support",
    iconColor: "text-amber-600",
  },
  "not-measured": {
    icon: null,
    color: "border-amber-600 bg-amber-50 text-amber-700",
    label: "Partial Support",
    iconColor: "text-amber-600",
  }
}

function getStatus(conf: number | null, analysis: string | null): VersionStatus {
  if (conf == null) return "not-measured"
  if (conf === 0) return "not-supported"
  if (conf !== null && conf > 0 && conf < 100) return "partial"
  if (analysis?.toLowerCase().includes("partial")) return "partial"
  if (conf === 100 || analysis?.toLowerCase().includes("support")) return "supported"
  return "not-supported"
}
export function NtpVersionAnalysis({ data }: { data: NTPVersionsData | null }) {
  const [hoveredVersion, setHoveredVersion] = useState<string | null>(null)

  if (!data) return <p className="text-gray-600">No version data available.</p>

  const renderVersion = (
    version: string,
    analysis: string | null,
    conf: number | null,
    responseVersion: string | null
  ) => {
    const status = getStatus(conf, analysis)
    const config = statusConfig[status]
    const isHovered = hoveredVersion === version

    return (
      <div
        key={version}
        className="ntp-version-wrapper"
        onMouseEnter={() => setHoveredVersion(version)}
        onMouseLeave={() => setHoveredVersion(null)}
      >
        <button className={`ntp-version-button ${status}`}>
          {config.icon && <config.icon className={`ntp-icon ${status}`} />}
          <span>{version}</span>
        </button>

        {isHovered && (
          <div className="ntp-tooltip">
            <h3 className="ntp-tooltip-title">{version} Analysis</h3>
            <p className="ntp-tooltip-description">
              {analysis || "No analysis available."}
            </p>
            {responseVersion && (
              <p className="ntp-tooltip-extra">
                <b>Response Version:</b> {responseVersion}
              </p>
            )}
            {conf !== null && (
              <p className="ntp-tooltip-extra">
                <b>Confidence:</b> {conf}%
              </p>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="ntp-container">
      <h1 className="ntp-title">NTP Version Analysis</h1>

      <div className="ntp-versions-container">
        {renderVersion("NTPv1", data.ntpv1_analysis, data.ntpv1_supported_conf, data.ntpv1_response_version)}
        {renderVersion("NTPv2", data.ntpv2_analysis, data.ntpv2_supported_conf, data.ntpv2_response_version)}
        {renderVersion("NTPv3", data.ntpv3_analysis, data.ntpv3_supported_conf, data.ntpv3_response_version)}
        {renderVersion("NTPv4", data.ntpv4_analysis, data.ntpv4_supported_conf, data.ntpv4_response_version)}
        {renderVersion("NTPv5", data.ntpv5_analysis, data.ntpv5_supported_conf, data.ntpv5_response_version)}
      </div>

      <div className="ntp-legend">
        {Object.entries(statusConfig).map(([key, config]) => (
          <div key={key} className="ntp-legend-item">
            {config.icon && <config.icon className={`ntp-legend-icon ${key}`} />}
            <span className="ntp-legend-label">{config.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}


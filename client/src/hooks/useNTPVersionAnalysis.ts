import { useEffect, useState } from "react"
import axios from "axios"
import { NTPVersionsData } from "../utils/types.ts"
import { transformJSONDataToNTPVerData} from "../utils/transformJSONDataToNTPverData"
const dummyData: NTPVersionsData = {
  id_vs: 1,

  id_v4_1: 101,
  id_v4_2: 102,
  id_v4_3: 103,
  id_v4_4: 104,
  id_v5: 201,

  ntpv1_response_version: "ntpv1",
  ntpv2_response_version: null,
  ntpv3_response_version: "ntpv3",
  ntpv4_response_version: "ntpv4",
  ntpv5_response_version: "ntpv5",

  ntpv1_supported_conf: 100,
  ntpv2_supported_conf: 0,
  ntpv3_supported_conf: 100,
  ntpv4_supported_conf: 100,
  ntpv5_supported_conf: 50,

  ntpv1_analysis: "NTPv1 responded successfully but lacks modern security features.",
  ntpv2_analysis: "NTPv2 is deprecated and not supported by this server.",
  ntpv3_analysis: "NTPv3 supported with stable timing accuracy.",
  ntpv4_analysis: "NTPv4 is fully supported — preferred version with best accuracy.",
  ntpv5_analysis: "NTPv5 partially supported; draft implementation detected.",

  ntpv4_1_measurement: {
    id: 101,
    ntpv_data: {
      server_name: "time.apple.com",
      offset: 0.134,
      rtt: 12.3,
      stratum: 1,
      country: "US",
      ip: "216.239.35.0",
    },
  },
  ntpv4_2_measurement: {
    id: 102,
    ntpv_data: {
      server_name: "time.apple.com",
      offset: 0.225,
      rtt: 10.1,
      stratum: 2,
      country: "NL",
      ip: "17.253.34.125",
    },
  },
  ntpv4_3_measurement: {
    id: 103,
    ntpv_data: {
      server_name: "time.apple.com",
      offset: 0.324,
      rtt: 15.7,
      stratum: 2,
      country: "DE",
      ip: "138.201.140.44",
    },
  },
  ntpv4_4_measurement: {
    id: 104,
    ntpv_data: {
      server_name: "time.apple.com",
      offset: 0.118,
      rtt: 8.9,
      stratum: 1,
      country: "US",
      ip: "162.159.200.1",
    },
  },
  ntpv5_measurement: {
    id: 201,
    draft_name: "draft-mlichvar-ntp-version-5-03",
    ntpv5_data: {
      server_name: "time.cloudflare.com",
      offset: 0.110,
      rtt: 7.5,
      stratum: 1,
      country: "US",
      ip: "162.159.200.1",
    },
    analysis: "Partial NTPv5 support detected; using experimental implementation.",
  },
};
export function useNtpVersionAnalysis(measurementId: number) {
  const [data, setData] = useState<NTPVersionsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!measurementId) return
    let interval: NodeJS.Timeout

    const fetchData = async () => {
      try {
        const response = await axios.get(`/measurements/ntp_versions/${measurementId}`)
        const transformed = transformJSONDataToNTPVerData(response.data ? response.data : dummyData)
        setData(dummyData)
        setLoading(false)

        // Stop polling if all analyses are filled
        if (transformed) {
          const analyses = [
            transformed.ntpv1_analysis,
            transformed.ntpv2_analysis,
            transformed.ntpv3_analysis,
            transformed.ntpv4_analysis,
            transformed.ntpv5_analysis,
          ]
          const allAvailable = analyses.every((a) => a && a.trim().length > 0)
          if (allAvailable && interval) clearInterval(interval)
        }
      } catch (err) {
        setError("Failed to load NTP version analysis.")
        setLoading(false)
      }
    }

    fetchData()
    interval = setInterval(fetchData, 5000)

    return () => clearInterval(interval)
  }, [measurementId])

  return { data, loading, error }
}
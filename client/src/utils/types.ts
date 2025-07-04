import { LatLngTuple } from "leaflet"

/**
 * Data type used for manipulating and using NTP information
 */
export type NTPData = {
  ntp_version: number
  vantage_point_ip: string
  ip: string
  server_name: string
  is_anycast: boolean
  country_code: string
  coordinates: LatLngTuple
  ntp_server_ref_parent_ip: string | null
  ref_id: string
  client_sent_time: [number,number]
  server_recv_time: [number,number]
  server_sent_time: [number,number]
  client_recv_time: [number,number]
  offset: number
  RTT: number
  stratum: number
  precision: number
  root_delay: number
  poll: number
  root_dispersion: number
  ntp_last_sync_time: [number,number]
  leap: number
  jitter: number | null
  nr_measurements_jitter: number
  asn_ntp_server: string
  time: number
}

/**
 * Data type used for determing measurement type in the visualization graphs
 */
export type Measurement = "RTT" | "offset"

/**
 * Data type used for manipulating and using RIPE information
 */
export type RIPEData = {
  measurementData : NTPData
  probe_addr_v4: string | null
  probe_addr_v6: string | null
  probe_id: string
  probe_country: string
  probe_location: LatLngTuple
  time_to_result: number
  got_results: boolean
  measurement_id: number
}

/**
 * Data type for the RIPE measurement trigger response
 */
export type RIPEResp = {
  measurementId: string | null
  vantage_point_ip: string | null
  coordinates: LatLngTuple | null
}

/**
 * A single place to remember everything we want to preserve
 * when the user leaves and re-enters the Home tab.
 * (Feel free to add more fields later – e.g. `selOption` –
 * just keep the shape in sync everywhere you use it.)
 */
export interface HomeCacheState {
  ntpData: NTPData | null
  chartData: Map<string, NTPData[]> | null
  measured: boolean
  selMeasurement: Measurement          // 'offset' | 'RTT'
  measurementId: string | null
  vantagePointInfo: [LatLngTuple,string] | null
  allNtpMeasurements: NTPData[] | null
  ripeMeasurementResp: RIPEData[] | null
  ripeMeasurementStatus: RipeStatus | null    // 'pending' | 'complete' | ...
  ipv6Selected: boolean
  isLoading: boolean                    // Track when NTP measurement is loading
  measurementSessionActive: boolean     // Track when any measurement session is active
}

export type RipeStatus = "pending" | "partial_results" | "complete" | "timeout" | "error"
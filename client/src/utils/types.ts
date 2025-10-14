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
  measurement_id: string | null
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

export type NTPResp = {
  measurement_id: string | null
}

/**
 * Data type for the RIPE measurement trigger response
 */
export type RIPEResp = {
  measurementId: string | null
  vantage_point_ip: string | null
  coordinates: LatLngTuple | null
}


export type NTPVersionsData = {
    id_vs: number

    id_v4_1: number | null
    id_v4_2: number | null
    id_v4_3: number | null
    id_v4_4: number | null
    id_v5: number | null

    ntpv1_response_version: string | null
    ntpv2_response_version: string | null
    ntpv3_response_version: string | null
    ntpv4_response_version: string | null
    ntpv5_response_version: string | null

    ntpv1_supported_conf: number | null
    ntpv2_supported_conf: number | null
    ntpv3_supported_conf: number | null
    ntpv4_supported_conf: number | null
    ntpv5_supported_conf: number | null

    ntpv1_analysis: string | null
    ntpv2_analysis: string | null
    ntpv3_analysis: string | null
    ntpv4_analysis: string | null
    ntpv5_analysis: string | null

}
/**
 * Data type for NTS measurement results
 */
export type NTSResult = Record<string, any>;

/**
 * A single place to remember everything we want to preserve
 * when the user leaves and re-enters the Home tab.
 * (Feel free to add more fields later – e.g. `selOption` –
 * just keep the shape in sync everywhere you use it.)
 */
export interface HomeCacheState {
  ntpData: NTPData | null
  ntsResult: NTSResult | null 
  ripeMeasurementResp: RIPEData[] | null
  versionData: NTPVersionsData | null

  chartData: Map<string, NTPData[]> | null
  measured: boolean
  selMeasurement: Measurement          // 'offset' | 'RTT'
  measurementId: string | null
  ripeMeasurementId: string | null     // RIPE measurement ID for reloading
  vantagePointInfo: [LatLngTuple,string] | null
  allNtpMeasurements: NTPData[] | null
  
  ripeMeasurementStatus: RipeStatus | null    // 'pending' | 'complete' | ...
  ipv6Selected: boolean
  isLoading: boolean                    // Track when NTP measurement is loading
  measurementSessionActive: boolean     // Track when any measurement session is active
  error: any

}

export type RipeStatus = "pending" | "partial_results" | "complete" | "timeout" | "error"

export type MeasurementRequest = {
  server: string;
  ipv6_measurement?: boolean;
  wanted_ip_type?: number;
  measurement_type?: string;
  ntp_versions_to_analyze?: string[] | null;
  analyse_all_ntp_versions?: boolean;
  ntp_versions_analysis_on_each_ip?: boolean;
  nts_analysis_on_each_ip?: boolean;
  ntpv5_draft?: string;
  custom_probes_asn?: string;
  custom_probes_country?: string;
  custom_client_ip?: string;
}

export type MeasurementStatus = "pending" | "RIPE" | "NTP" | "NTS" | "NTPver" | "finished" | "failed";
export type FullMeasurementResult = {
  status: MeasurementStatus;
  mainMeasurement: any; 
  ipMeasurements?: any[]; // only for DN
  ripeData?: any;
  ntsData?: any; // optional
  ntpVersions?: any;
  error?: Error;
}

export type PartialMeasurementResult = {
  id: string; 
  status: MeasurementStatus; 
  id_ripe?: number | null;   
  id_nts?: number | null;    
  ip_measurements_ids?: { search_id: string }[]; //only for DN
 
};



//DELETE THIS ONCE NTP VERSION ANALYSIS BEHAVIOUR IS FINISHED
export const dummyData: NTPVersionsData = {
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
  ntpv3_supported_conf: null,
  ntpv4_supported_conf: 100,
  ntpv5_supported_conf: 50,

  ntpv1_analysis: "NTPv1 responded successfully but lacks modern security features.",
  ntpv2_analysis: "NTPv2 is deprecated and not supported by this server.",
  ntpv3_analysis: "",
  ntpv4_analysis: "NTPv4 is fully supported — preferred version with best accuracy.",
  ntpv5_analysis: "NTPv5 partially supported; draft implementation detected.",

  
};
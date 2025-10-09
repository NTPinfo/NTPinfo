import { NTPData } from "./types.ts"

/**
 * Function to convert the received measurement or single historical data JSON into an NTPData datapoint.
 * All values are extracted directly from the JSON file, with the exception of time.
 * Time is converted from the NTP Epoch to the UNIX Epoch before being stored.
 * @param fetchedData the JSON which will be received from the measurement or historical data endpoint.
 * @returns a single NTPData filled with information extracted from the JSON, or null if there is no JSON.
 */
export const transformJSONDataToNTPData = (fetchedData: any): NTPData | null => {
    if (!fetchedData) 
        return null
    
    return {
        ntp_version: fetchedData.ntp_version,
        vantage_point_ip: fetchedData.vantage_point_ip,
        ip: fetchedData.ntp_server_ip,
        server_name: fetchedData.ntp_server_name,
        is_anycast: fetchedData.ntp_server_location.ip_is_anycast,
        country_code: fetchedData.ntp_server_location.country_code,
        coordinates: [fetchedData.ntp_server_location.coordinates[0],fetchedData.ntp_server_location.coordinates[1]],
        ntp_server_ref_parent_ip: fetchedData.ntp_server_ref_parent_ip,
        ref_id: fetchedData.ref_name ?? fetchedData.ntp_server_ref_parent_ip,
        client_sent_time: [fetchedData.client_sent_time.seconds, fetchedData.client_sent_time.fraction],
        server_recv_time: [fetchedData.server_recv_time.seconds, fetchedData.server_recv_time.fraction],
        server_sent_time: [fetchedData.server_sent_time.seconds, fetchedData.server_sent_time.fraction],
        client_recv_time: [fetchedData.client_recv_time.seconds, fetchedData.client_recv_time.fraction],
        offset: Number((fetchedData.offset * 1000).toFixed(3)),
        RTT: Number((fetchedData.rtt * 1000).toFixed(3)),
        stratum: fetchedData.stratum,
        precision: fetchedData.precision,
        root_delay: fetchedData.root_delay,
        poll: fetchedData.poll,
        root_dispersion: fetchedData.root_dispersion,
        ntp_last_sync_time: [fetchedData.ntp_last_sync_time.seconds, fetchedData.ntp_last_sync_time.fraction],
        leap: fetchedData.leap,
        jitter: fetchedData.jitter,
        nr_measurements_jitter: fetchedData.nr_measurements_jitter,
        asn_ntp_server: fetchedData.asn_ntp_server,
        time: (fetchedData.client_sent_time.seconds - 2208988800) * 1000,
        measurement_id: fetchedData.id
    }
}
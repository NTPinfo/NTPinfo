import { NTPData } from "./types.ts"
import { RIPEData } from "./types.ts"

/**
 * A function to convert the received RIPE measurement JSON to a RIPEData datapoint.
 * All values are extracted directly from the JSON file, with a few exceptions.
 * Time is converted from the NTP Epoch to the UNIX Epoch before being stored.
 * Some fields that do not appear in the JSON are hardcoded to empty or -1
 * offset and RTT are multiplied by 1000 since they are sent in seconds instead of ms.
 * got_results is filled as a boolean to indicate whether the probe sucessfully finished its measurement, as we could receive probes with no measurement values.
 * By our set convention, -1 is the default value in the measurement fields, and it indicates that the measurement was not completed by the probe.
 * The measurement ID is stored here as well as in the trigger for showing it together will all the other results.
 * @param fetchedData the JSON which will be received from the RIPE measurement endpoint.
 * @returns A single RIPEData datapoint filled with information extracted from the JSON, or null if there is no JSON
 */
export const transformJSONDataToRIPEData = (fetchedData: any): RIPEData | null => {
    if (!fetchedData || !Array.isArray(fetchedData.result) || fetchedData.result.length === 0) {
        return null
    }

    const measurement = fetchedData.result[0]

    const NTP_TO_UNIX_EPOCH_OFFSET = 2208988800;
    const clientSentTimeNtp = measurement.client_sent_time;

    const clientSentSeconds = Math.floor(clientSentTimeNtp / 2 ** 32);
    const clientSentFraction = clientSentTimeNtp % 2 ** 32;
    const clientSentMs = (clientSentSeconds - NTP_TO_UNIX_EPOCH_OFFSET) * 1000 + (clientSentFraction / 2 ** 32) * 1000;

    const measurementData: NTPData = {
        ntp_version: fetchedData.ntp_version,
        vantage_point_ip: fetchedData.vantage_point_ip,
        ip: fetchedData.ntp_server_ip,
        server_name: fetchedData.ntp_server_name, 
        is_anycast: fetchedData.ntp_server_location.ip_is_anycast,
        country_code: fetchedData.ntp_server_location.country_code,
        coordinates: [fetchedData.ntp_server_location.coordinates[0],fetchedData.ntp_server_location.coordinates[1]],
        ntp_server_ref_parent_ip: "", 
        ref_id: fetchedData.ref_id,
         client_sent_time: measurement.client_sent_time,
        server_recv_time: measurement.server_recv_time,
        server_sent_time: measurement.server_sent_time,
        client_recv_time: measurement.client_recv_time,
        offset: Number((measurement.offset * 1000).toFixed(3)),
        RTT: Number((measurement.rtt * 1000).toFixed(3)), 
        stratum: fetchedData.stratum,
        precision: fetchedData.precision,
        root_delay: fetchedData.root_delay,
        poll: fetchedData.poll,
        root_dispersion: fetchedData.root_dispersion,
        ntp_last_sync_time: -1,
        leap: -1,
        jitter: -1,
        nr_measurements_jitter: -1,
        asn_ntp_server: fetchedData.asn_ntp_server,
        time: clientSentMs,
        measurement_id: fetchedData.id
    }
    return{
        measurementData: measurementData,
        probe_addr_v4: fetchedData.probe_addr.ipv4,
        probe_addr_v6: fetchedData.probe_addr.ipv6,
        probe_id: fetchedData.probe_id,
        probe_country: fetchedData.probe_location.country_code,
        probe_location: [fetchedData.probe_location.coordinates[1], fetchedData.probe_location.coordinates[0]],
        time_to_result: fetchedData.time_to_result,
        got_results: measurement.rtt !== -1,
        measurement_id: fetchedData.ripe_measurement_id
    }
}
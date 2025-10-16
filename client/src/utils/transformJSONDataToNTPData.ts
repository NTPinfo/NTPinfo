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

    const safeNum = (v: any, fallback = 0): number =>
      typeof v === "number" && !Number.isNaN(v) ? v : fallback;
    const loc = fetchedData.ntp_server_location ?? {}
    const isAnycast = Boolean(loc?.ip_is_anycast)
    const countryCode = loc?.country_code ?? ""
    const coordsX = typeof loc?.coordinates_x === "number" ? loc.coordinates_x : 25.0
    const coordsY = typeof loc?.coordinates_y === "number" ? loc.coordinates_y : -71.0
    const asn = loc?.asn_ntp_server ?? ""

    //here we will calculate the "time" when in right format.
    const NTP_TO_UNIX_EPOCH_OFFSET = 2208988800;
    const clientSentTimeNtp = fetchedData.client_sent_time;

    const clientSentSeconds = Math.floor(clientSentTimeNtp / 2 ** 32);
    const clientSentFraction = clientSentTimeNtp % 2 ** 32;
    const clientSentMs = (clientSentSeconds - NTP_TO_UNIX_EPOCH_OFFSET) * 1000 + (clientSentFraction / 2 ** 32) * 1000;


    const ans: NTPData =  {
        ntp_version: fetchedData.version,
        vantage_point_ip: fetchedData.vantage_point_ip,
        ip: fetchedData.measured_server_ip ?? "",
        server_name: fetchedData.host ?? "",
        is_anycast: isAnycast,
        country_code: countryCode,
        coordinates: [coordsX, coordsY],
        ntp_server_ref_parent_ip: fetchedData.ref_id,
        ref_id: fetchedData.ref_id ?? "",
        client_sent_time: fetchedData.client_sent_time,
        server_recv_time: fetchedData.server_recv_time,
        server_sent_time: fetchedData.server_sent_time,
        client_recv_time: fetchedData.client_recv_time,
        offset: Number((fetchedData.offset * 1000).toFixed(3)),
        RTT: Number((fetchedData.rtt * 1000).toFixed(3)),
        stratum: fetchedData.stratum,
        precision: safeNum(fetchedData.precision, 0),
        root_delay: safeNum(fetchedData.root_delay, 0),
        poll: fetchedData.poll,
        root_dispersion: fetchedData.root_disp,
        ntp_last_sync_time: fetchedData.ref_time,
        leap: fetchedData.leap,
        jitter: 0,
        nr_measurements_jitter: 0,
        asn_ntp_server: asn,
        time: clientSentMs,
        measurement_id: fetchedData.id
    };
    return ans;
}
import { NTPData } from "./types";

// Transforms server full measurement main_measurement to NTPData
export const transformFullMeasurementMainToNTPData = (m: any): NTPData | null => {
  if (!m) return null;

  const clientSentUnix = typeof m.client_sent_time === 'number' ? m.client_sent_time : null;
  const serverRecvUnix = typeof m.server_recv_time === 'number' ? m.server_recv_time : null;
  const serverSentUnix = typeof m.server_sent_time === 'number' ? m.server_sent_time : null;
  const clientRecvUnix = typeof m.client_recv_time === 'number' ? m.client_recv_time : null;
  const refTimeUnix = typeof m.ref_time === 'number' ? m.ref_time : null;

  // Backend returns offset/rtt likely in seconds; we normalize to ms for UI consistency
  const toMs = (v: any) => (typeof v === 'number' ? Number((v * 1000).toFixed(3)) : v);

  return {
    ntp_version: m.version,
    vantage_point_ip: m.ntp_server_location.vantage_point_ip ?? "",
    ip: m.measured_server_ip ?? m.host ?? "",
    server_name: m.host ?? "",
    is_anycast: m.ntp_server_location.ip_is_anycast,
    country_code: m.ntp_server_location.country_code,
    coordinates: [m.ntp_server_location.coordinates_x, m.ntp_server_location.coordinates_y],
    ntp_server_ref_parent_ip: m.ntp_server_ref_parent_ip,
    ref_id: m.ref_id ?? "",
    client_sent_time: clientSentUnix ?? -1,
    server_recv_time: serverRecvUnix ?? -1,
    server_sent_time: serverSentUnix ?? -1,
    client_recv_time: clientRecvUnix ?? -1,
    offset: toMs(m.offset),
    RTT: toMs(m.rtt),
    stratum: m.stratum ?? -1,
    precision: m.precision ?? 0,
    root_delay: m.root_delay ?? 0,
    poll: m.poll ?? 0,
    root_dispersion: m.root_disp ?? 0,
    ntp_last_sync_time: refTimeUnix ?? -1,
    leap: m.leap ?? 0,
    jitter: null,
    nr_measurements_jitter: 0,
    asn_ntp_server: m.ntp_server_location.asn_ntp_server,
    time: clientSentUnix ? clientSentUnix * 1000 : Date.now(),
    measurement_id: String(m.id ?? "")
  };
};




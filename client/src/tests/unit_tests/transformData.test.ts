import { expect, test, describe } from 'vitest'
import { transformJSONDataToNTPData } from '../../utils/transformJSONDataToNTPData'
import { transformJSONDataToRIPEData } from '../../utils/transformJSONDataToRIPEData'

describe("transform JSON Data to NTP Data", () => {
    test("tranform to NTP Data", () => {
    const fetchedData = {
        version: 4,
        offset: 0.001,
        rtt: 0.001,
        stratum: 2,
        jitter: 0.0005,
        precision: -20,
        poll: 6,
        root_disp: 0.01,
        root_delay: 0.02,
        client_sent_time: { seconds: 3900000000, fraction: 123456789 },
        server_recv_time: { seconds: 3900000000, fraction: 123556789 },
        server_sent_time: { seconds: 3900000000, fraction: 123656789 },
        client_recv_time: { seconds: 3900000000, fraction: 123756789 },
        ntp_server_ip: "192.168.0.1",
        ntp_server_name: "pool.ntp.org",
        ref_name: null,
        ref_id: "10.0.0.1",
        ntp_last_sync_time: { seconds: 3899990000, fraction: 0 },
        leap: 0,
        vantage_point_ip: "203.0.113.42",
        ntp_server_location: {
            coordinates_x: 48.8566,
            coordinates_y: 2.3522,
            country_code: "FR",
            asn_ntp_server: "6185",
            ip_is_anycast: false
        },
        nr_measurements_jitter: 16,
        id: "dn1"
    }

    const res = transformJSONDataToNTPData(fetchedData)

    expect(res?.ntp_version).toBe(fetchedData.version)
    expect(res?.offset).toBeCloseTo(fetchedData.offset * 1000, 3)
    expect(res?.RTT).toBeCloseTo(fetchedData.rtt * 1000, 3)
    expect(res?.stratum).toBe(fetchedData.stratum)
    expect(res?.jitter).toBe(0)
    expect(res?.precision).toBe(fetchedData.precision)
    expect(res?.poll).toBe(fetchedData.poll)
    expect(res?.root_dispersion).toBe(fetchedData.root_disp)
    expect(res?.root_delay).toBe(fetchedData.root_delay)
    expect(res?.ntp_server_ref_parent_ip).toBe(fetchedData.ref_id)
    expect(res?.ref_id).toBe(fetchedData.ref_id)
    expect(res?.leap).toBe(fetchedData.leap)
    expect(res?.vantage_point_ip).toBe(fetchedData.vantage_point_ip)
    expect(res?.coordinates[0]).toBe(fetchedData.ntp_server_location.coordinates_x)
    expect(res?.coordinates[1]).toBe(fetchedData.ntp_server_location.coordinates_y)
    expect(res?.country_code).toBe(fetchedData.ntp_server_location.country_code)
    expect(res?.is_anycast).toBe(fetchedData.ntp_server_location.ip_is_anycast)
    expect(res?.asn_ntp_server).toBe(fetchedData.ntp_server_location.asn_ntp_server)
})

    test("Return null on null input", () => {
        expect(transformJSONDataToNTPData(null)).toBeNull()
    })
})

describe('transform JSON Data to RIPE Data', () => {
    test("tranform to RIPE Data Success", () => {
    const input = {
    ntp_version: 4,
    vantage_point_ip: "192.0.2.50",
    ntp_server_ip: "192.0.2.1",
    ntp_server_name: "ntp.example.com",
    stratum: 2,
    precision: -20,
    root_dispersion: 0.1,
    root_delay: 0.05,
    asn_ntp_server: "6185",
    poll: 6,
    ref_id: "GPS",
    probe_addr: { ipv4: "203.0.113.5", ipv6: "2001:db8::5" },
    probe_id: 12345,
    probe_location: {
      country_code: "NL",
      coordinates: [4.895168, 52.370216]
    },
    ripe_measurement_id: 67890,
    ntp_server_location: {
      coordinates: [50.262, 4.333],
      country_code: "DE",
      ip_is_anycast: true
    },
    time_to_result: 1.234,
    result: [
      {
        offset: 0.00123,
        rtt: 0.00456,
        client_sent_time: { seconds: 3792998400, fraction: 111 },
        server_recv_time: { seconds: 3792998400, fraction: 222 },
        server_sent_time: { seconds: 3792998400, fraction: 333 },
        client_recv_time: { seconds: 3792998400, fraction: 444 },
      }
    ]
  }

    const result = transformJSONDataToRIPEData(input);

  expect(result).not.toBeNull()
  expect(result!.measurementData.ntp_version).toBe(4)
  expect(result!.measurementData.vantage_point_ip).toBe("192.0.2.50")
  expect(result!.measurementData.ip).toBe("192.0.2.1")
  expect(result!.measurementData.server_name).toBe("ntp.example.com")
  expect(result!.measurementData.is_anycast).toBe(true)
  expect(result!.measurementData.country_code).toBe("DE")
  expect(result!.measurementData.coordinates).toEqual([50.262, 4.333])
  expect(result!.measurementData.ntp_server_ref_parent_ip).toBe("")
  expect(result!.measurementData.ref_id).toBe("GPS")

  expect(result!.measurementData.client_sent_time).toEqual([3792998400, 111])
  expect(result!.measurementData.server_recv_time).toEqual([3792998400, 222])
  expect(result!.measurementData.server_sent_time).toEqual([3792998400, 333])
  expect(result!.measurementData.client_recv_time).toEqual([3792998400, 444])

  expect(result!.measurementData.offset).toBeCloseTo(1.23)
  expect(result!.measurementData.RTT).toBeCloseTo(4.56)
  expect(result!.measurementData.stratum).toBe(2)
  expect(result!.measurementData.precision).toBe(-20)
  expect(result!.measurementData.root_delay).toBe(0.05)
  expect(result!.measurementData.poll).toBe(6)
  expect(result!.measurementData.root_dispersion).toBe(0.1)
  expect(result!.measurementData.ntp_last_sync_time).toEqual([-1, -1])
  expect(result!.measurementData.leap).toBe(-1)
  expect(result!.measurementData.jitter).toBe(-1)
  expect(result!.measurementData.nr_measurements_jitter).toBe(-1)
  expect(result!.measurementData.time).toBe((3792998400 - 2208988800) * 1000)
  expect(result!.measurementData.asn_ntp_server).toBe("6185")

  expect(result!.probe_addr_v4).toBe("203.0.113.5")
  expect(result!.probe_addr_v6).toBe("2001:db8::5")
  expect(result!.probe_id).toBe(12345)
  expect(result!.probe_country).toBe("NL")
  expect(result!.probe_location).toEqual([52.370216, 4.895168])
  expect(result!.time_to_result).toBe(1.234)
  expect(result!.got_results).toBe(true)
  expect(result!.measurement_id).toBe(67890)
})

  test('Return null on null input', () => {
    expect(transformJSONDataToRIPEData(null)).toBeNull()
  })

  test('Return null on empty input or result', () => {
    expect(transformJSONDataToRIPEData({})).toBeNull()
    expect(transformJSONDataToRIPEData({ result: [] })).toBeNull()
  })
})


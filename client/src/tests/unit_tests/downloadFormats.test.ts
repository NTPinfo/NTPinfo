import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { downloadJSON, downloadCSV } from '../../utils/downloadFormats'
import type { NTPData, RIPEData } from '../../utils/types'

describe('Test Download Formats', () => {
  const mockCreateObjectURL = vi.fn(() => 'blob:http://localhost/blobid')
  const mockRevokeObjectURL = vi.fn()
  const mockClick = vi.fn()

  beforeEach(() => {
    // Stub URL methods
    vi.stubGlobal('URL', {
      createObjectURL: mockCreateObjectURL,
      revokeObjectURL: mockRevokeObjectURL,
    })

    // Stub document.createElement and mock <a> click
    vi.stubGlobal('document', {
      ...document,
      createElement: vi.fn(() => ({
        href: '',
        download: '',
        click: mockClick,
      })),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  const ntpData: NTPData = {
    ntp_version: 4,
    measurement_id: "dn1",
    vantage_point_ip: "192.0.2.1",
    ip: "203.0.113.10",
    server_name: "time.example.net",
    is_anycast: false,
    country_code: "US",
    coordinates: [37.7749, -122.4194],
    ntp_server_ref_parent_ip: "198.51.100.1",
    ref_id: "GPS",
    client_sent_time: 1718277600,
    server_recv_time: 1718277600,
    server_sent_time: 1718277600,
    client_recv_time: 1718277600,
    offset: 0.0001,
    RTT: 0.0004,
    stratum: 1,
    precision: -20,
    root_delay: 0.00003,
    poll: 6,
    root_dispersion: 0.00008,
    ntp_last_sync_time: 1718277500,
    leap: 0,
    jitter: 0.00002,
    nr_measurements_jitter: 12,
    asn_ntp_server: "6185",
    time: 1718277600.1238
  }

  const ripeData: RIPEData = {
    measurementData: ntpData,
    probe_addr_v4: "203.0.113.10",
    probe_addr_v6: "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
    probe_id: "42",
    probe_country: 'NL',
    probe_location: [52.37, 4.89],
    time_to_result: 69,
    got_results: true,
    measurement_id: 123456,
  }

  test('Test Download JSON file', () => {
    downloadJSON([ntpData, ripeData])
    expect(mockCreateObjectURL).toHaveBeenCalled()
    expect(mockClick).toHaveBeenCalled()
    expect(mockRevokeObjectURL).toHaveBeenCalled()
  })

  test('Test Download CSV file', () => {
    downloadCSV([ntpData, ripeData])
    expect(mockCreateObjectURL).toHaveBeenCalled()
    expect(mockClick).toHaveBeenCalled()
    expect(mockRevokeObjectURL).toHaveBeenCalled()
  })
})
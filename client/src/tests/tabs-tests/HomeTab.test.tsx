import HomeTab from "../../tabs/HomeTab"
import { render, screen } from '@testing-library/react'
import { describe, test, expect, vi, beforeEach, Mock } from 'vitest'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { useFetchIPData } from '../../hooks/useFetchIPData.ts'
import { useFetchHistoricalIPData } from '../../hooks/useFetchHistoricalIPData.ts'
import { useFetchRIPEData } from '../../hooks/useFetchRipeData.ts'
import { useTriggerRipeMeasurement } from '../../hooks/useTriggerRipeMeasurement.ts'
import { downloadJSON, downloadCSV } from '../../utils/downloadFormats.ts'
import { HomeCacheState, NTPData, Measurement, RIPEData } from '../../utils/types'

vi.mock('../../hooks/useFetchIPData.ts', () => ({
  useFetchIPData: vi.fn()
}))

vi.mock('../../hooks/useFetchHistoricalIPData.ts', () => ({
  useFetchHistoricalIPData: vi.fn()
}))

vi.mock('../../hooks/useFetchRipeData.ts', () => ({
  useFetchRIPEData: vi.fn()
}))

vi.mock('../../hooks/useTriggerRipeMeasurement.ts', () => ({
  useTriggerRipeMeasurement: vi.fn()
}))

vi.mock('../../utils/downloadFormats.ts', () => ({
  downloadJSON: vi.fn(),
  downloadCSV: vi.fn()
}))

vi.mock('../../components/WorldMap.tsx', () => ({
  default: (props: any) => (
    <div data-testid="world-map">
      <div data-testid="map-status">{props.status}</div>
      {props.probes && <div data-testid="map-probes">Probes: {props.probes.length}</div>}
      {props.ntpServers && <div data-testid="map-servers">Servers: {props.ntpServers.length}</div>}
      {props.vantagePointInfo && <div data-testid="map-vantage">Vantage Point Available</div>}
    </div>
  )
}))

vi.mock('../../components/LineGraph.tsx', () => ({
  default: (props: any) => (
    <div data-testid="line-graph">
      <div data-testid="graph-measurement">{props.selectedMeasurement}</div>
      <div data-testid="graph-option">{props.selectedOption}</div>
    </div>
  )
}))

describe('HomeTab', () => {

    const mockNTPData: NTPData = {
        ntp_version: 4,
        vantage_point_ip: "192.0.2.123",
        ip: "203.0.113.5",
        server_name: "ntp.example.org",
        is_anycast: false,
        country_code: "NL",
        coordinates: [52.3676, 4.9041],
        ntp_server_ref_parent_ip: "203.0.113.1",
        ref_id: "GPS",
        client_sent_time: [1687000000, 123456789],
        server_recv_time: [1687000000, 123456999],
        server_sent_time: [1687000000, 123457199],
        client_recv_time: [1687000000, 123457399],
        offset: -2.345,
        RTT: 1.543,
        stratum: 2,
        precision: -23,
        root_delay: 0.125,
        poll: 6,
        root_dispersion: 0.256,
        ntp_last_sync_time: [1686999900, 987654321],
        leap: 0,
        jitter: 0.321,
        nr_measurements_jitter: 5,
        time: 1687000000,
        asn_ntp_server: "6541",
        measurement_id: "dn1"
    }

    const mockRIPEData: RIPEData = {
        measurementData: {
            ntp_version: 4,
            vantage_point_ip: "198.51.100.45",
            ip: "203.0.113.6",
            server_name: "ntp.example.org",
            is_anycast: false,
            country_code: "DE",
            coordinates: [50.1109, 8.6821],
            ntp_server_ref_parent_ip: "203.0.113.1",
            ref_id: "GPS",
            client_sent_time: [1687000050, 223456789],
            server_recv_time: [1687000050, 223456999],
            server_sent_time: [1687000050, 223457199],
            client_recv_time: [1687000050, 223457399],
            offset: -1.123,
            RTT: 1.234,
            stratum: 2,
            precision: -23,
            root_delay: 0.144,
            poll: 6,
            root_dispersion: 0.189,
            ntp_last_sync_time: [1686999950, 876543210],
            leap: 0,
            jitter: 0.210,
            nr_measurements_jitter: 6,
            time: 1687000050.223456,
            asn_ntp_server: "6541", 
            measurement_id: "dn1"
        },
        probe_addr_v4: "198.51.100.45",
        probe_addr_v6: "::1",
        probe_id: "24567",
        probe_country: "DE",
        probe_location: [50.1109, 8.6821],
        time_to_result: 3.75,
        got_results: true,
        measurement_id: 10293847
    }

    const initialCache: HomeCacheState = {
        ntpData: null,
        chartData: null,
        measured: false,
        selMeasurement: 'offset' as Measurement,
        measurementId: null,
        vantagePointInfo: null,
        allNtpMeasurements: null,
        ripeMeasurementResp: null,
        ripeMeasurementStatus: null,
        ipv6Selected: false,
        isLoading: false,
        ntsResult: null,
        versionData: null,
        ripeMeasurementId: null,
        error: null,
        measurementSessionActive: false
    }

    let mockSetCache: Mock
    let mockOnVisualizationDataChange: Mock

    let mockFetchIPData: Mock
    let mockFetchHistoricalIPData: Mock
    let mockUseFetchRIPEData: Mock
    let mockTriggerRipeMeasurement: Mock

    beforeEach(() => {
        vi.clearAllMocks()

        mockSetCache = vi.fn()
        mockOnVisualizationDataChange = vi.fn()

        mockFetchIPData = vi.fn().mockResolvedValue([mockNTPData])
        mockFetchHistoricalIPData = vi.fn().mockResolvedValue([mockNTPData])
        mockTriggerRipeMeasurement = vi.fn().mockResolvedValue({
        parsedData: {
            measurementId: 'test-measurement-123',
            vantage_point_ip: '192.168.1.1',
            coordinates: [52.3676, 4.9041]
        }
        })

        ;(useFetchIPData as Mock).mockReturnValue({
            fetchData: mockFetchIPData,
            loading: false,
            error: null,
            httpStatus: 200
        })

        ;(useFetchHistoricalIPData as Mock).mockReturnValue({
            fetchData: mockFetchHistoricalIPData
        })

        mockUseFetchRIPEData = vi.fn().mockReturnValue({
            result: null,
            status: null,
            error: null
        })
        ;(useFetchRIPEData as Mock).mockImplementation(mockUseFetchRIPEData)

        ;(useTriggerRipeMeasurement as Mock).mockReturnValue({
            triggerMeasurement: mockTriggerRipeMeasurement
        })
    })

    const setupTab = (cache: Partial<HomeCacheState> = {}) => {
    const completeCache = { ...initialCache, ...cache }
    return render(
      <HomeTab
        cache={completeCache}
        setCache={mockSetCache}
        onVisualizationDataChange={mockOnVisualizationDataChange}
      />
    )}


    test('Initial Render', () => {
        setupTab()

        expect(screen.getByText(/Privacy Notice/i)).toBeInTheDocument()
        expect(screen.getByText(/NTPinfo/i)).toBeInTheDocument()
        expect(screen.getByText(/Enter the domain name or IP address of the NTP server you want to measure./i)).toBeInTheDocument()
        expect(screen.getByPlaceholderText(/time.google.com/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /measure/i })).toBeInTheDocument()

        const ipv6ToggleButton = screen.getByLabelText(/ipv6/i)
        expect(ipv6ToggleButton).toBeInTheDocument()
        expect(ipv6ToggleButton).not.toBeChecked()
    })

    describe('User Interaction', () => {

        test('Start measurement with input', async () => {
            const user = userEvent.setup()
            setupTab()

            const serverInput = screen.getByPlaceholderText(/time.google.com/i)
            const measureButton = screen.getByRole('button', { name: /measure/i })

            await user.type(serverInput, 'time.google.com')
            await user.click(measureButton)

            
        })

        test('Check IPv6', async () => {
            const user = userEvent.setup()
            setupTab()

            const ipv6Toggle = screen.getByLabelText(/ipv6/i)
            await user.click(ipv6Toggle)

            expect(mockSetCache).toHaveBeenCalledWith(expect.any(Function))
            const updateFunction = mockSetCache.mock.calls[0][0]
            // Test that the update function correctly merges { ipv6Selected: true } with the previous state
            const result = updateFunction({ ipv6Selected: true })
            expect(result.ipv6Selected).toBe(true)
        })

        test('Button disabled with empty input', () => {
            const user = userEvent.setup()
            setupTab()

            const measureButton = screen.getByRole('button', { name: /measure/i })
            user.click(measureButton)


            expect(mockFetchIPData).not.toHaveBeenCalled()
            expect(mockFetchHistoricalIPData).not.toHaveBeenCalled()
        })

        test('Show loading and disable button', () => {
            ;(useFetchIPData as Mock).mockReturnValue({
            fetchData: mockFetchIPData,
            loading: true,
            error: null,
            httpStatus: 200
        })
        setupTab({measured: true})

    

        expect(screen.getByRole('button', { name: /measure/i })).toBeDisabled()
        })
    })

    describe('Display results', () => {
        test('Proper results and graph display after measurements', () => {

            const chartData = new Map<string, NTPData[]>()
            chartData.set('time.apple.com', [mockNTPData])

            setupTab({ ntpData: mockNTPData,
                       chartData: chartData,
                       measured: true,
                       ripeMeasurementResp: [mockRIPEData],
                       ripeMeasurementStatus: 'complete',
                       allNtpMeasurements: [mockNTPData],
                       vantagePointInfo: [[52.3676, 4.9041], '192.168.1.1'] })

            expect(screen.getByText('Results')).toBeInTheDocument()

            expect(screen.getByText(`${mockNTPData.offset} ms`)).toBeInTheDocument()
            expect(screen.getByText(`${mockNTPData.RTT} ms`)).toBeInTheDocument()

            expect(screen.getByTestId('line-graph')).toBeInTheDocument()
            expect(screen.getByTestId('graph-measurement')).toHaveTextContent('offset')
            expect(screen.getByTestId('graph-option')).toHaveTextContent('Last Day')

            expect(screen.getByRole('button', { name: /Download JSON/i })).toBeInTheDocument()
            expect(screen.getByRole('button', { name: /Download CSV/i })).toBeInTheDocument()

            expect(screen.getByTestId('world-map')).toBeInTheDocument()
            expect(screen.getByTestId('map-status')).toHaveTextContent('complete')
            expect(screen.getByTestId('map-probes')).toHaveTextContent('Probes: 1')
            expect(screen.getByTestId('map-servers')).toHaveTextContent('Servers: 1')
            expect(screen.getByTestId('map-vantage')).toBeInTheDocument()
        })
    })

    describe('Buttons functionality', () => {
        test('Download CSV', async () => {
            const user = userEvent.setup()
            setupTab({
                ntpData: mockNTPData,
                measured: true
            })

            const downloadButton = screen.getByRole('button', { name: /Download CSV/i })
            await user.click(downloadButton)

            expect(downloadCSV).toHaveBeenCalledWith([mockNTPData])
        })

        test('Download JSON and include RIPE', async () => {
            const user = userEvent.setup()
            setupTab({
                ntpData: mockNTPData,
                ripeMeasurementResp: [mockRIPEData],
                measured: true
            })

            const downloadButton = screen.getByRole('button', { name: /Download JSON/i })
            await user.click(downloadButton)

            expect(downloadJSON).toHaveBeenCalledWith([mockNTPData, mockRIPEData])
        })
    })
})
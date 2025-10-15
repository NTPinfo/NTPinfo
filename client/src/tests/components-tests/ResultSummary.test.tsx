// import { render, screen} from '@testing-library/react'
// import ResultSummary from '../../components/ResultSummary'
// import {describe, expect, test } from 'vitest'
// import '@testing-library/jest-dom'
// import { NTPData, RIPEData} from '../../utils/types'
// describe('ResultSummary', () => {
//     const mockNTPData: NTPData = {
//         ntp_version: 4,
//         vantage_point_ip: "192.0.2.123",
//         ip: "203.0.113.5",
//         server_name: "ntp.example.org",
//         is_anycast: false,
//         country_code: "NL",
//         coordinates: [52.3676, 4.9041],
//         ntp_server_ref_parent_ip: "203.0.113.1",
//         ref_id: "GPS",
//         client_sent_time: [1687000000, 123456789],
//         server_recv_time: [1687000000, 123456999],
//         server_sent_time: [1687000000, 123457199],
//         client_recv_time: [1687000000, 123457399],
//         offset: -2.345,
//         RTT: 1.543,
//         stratum: 2,
//         precision: -23,
//         root_delay: 0.125,
//         poll: 6,
//         root_dispersion: 0.256,
//         ntp_last_sync_time: [1686999900, 987654321],
//         leap: 0,
//         jitter: 0.321,
//         nr_measurements_jitter: 5,
//         time: 1687000000,
//         asn_ntp_server: "6541"
//     }   
//     const mockRIPEData: RIPEData = {
//         measurementData: {
//             ntp_version: 4,
//             vantage_point_ip: "198.51.100.45",
//             ip: "203.0.113.6",
//             server_name: "ntp.example.org",
//             is_anycast: false,
//             country_code: "DE",
//             coordinates: [50.1109, 8.6821],
//             ntp_server_ref_parent_ip: "203.0.113.1",
//             ref_id: "GPS",
//             client_sent_time: [1687000050, 223456789],
//             server_recv_time: [1687000050, 223456999],
//             server_sent_time: [1687000050, 223457199],
//             client_recv_time: [1687000050, 223457399],
//             offset: -1.123,
//             RTT: 1.234,
//             stratum: 2,
//             precision: -23,
//             root_delay: 0.144,
//             poll: 6,
//             root_dispersion: 0.189,
//             ntp_last_sync_time: [1686999950, 876543210],
//             leap: 0,
//             jitter: 0.210,
//             nr_measurements_jitter: 6,
//             time: 1687000050.223456,
//             asn_ntp_server: "6541"
//         },
//         probe_addr_v4: "198.51.100.45",
//         probe_addr_v6: "::1",
//         probe_id: "24567",
//         probe_country: "DE",
//         probe_location: [50.1109, 8.6821],
//         time_to_result: 3.75,
//         got_results: true,
//         measurement_id: 10293847,
//     }

//     test('Render results with status code 200', () => {
//         render(<ResultSummary data={mockNTPData} ripeData={mockRIPEData} 
//                               err={null} httpStatus={200} errMessage={null}
//                               ripeErr={null} ripeStatus={"complete"}/>)
        
//         expect(screen.getByText(/From Our NTP Client/i)).toBeInTheDocument()
//         expect(screen.getByText(/From the RIPE Atlas probe/i)).toBeInTheDocument()

//         const expectedRTT = screen.getAllByText(/Round-trip time/i)
//         expect(expectedRTT.length).toBe(2)
//         for (const element of expectedRTT)
//             expect(element).toBeInTheDocument()

//         const expectedOffset = screen.getAllByText('Offset')
//         expect(expectedOffset.length).toBe(2)
//         for (const element of expectedOffset)
//             expect(element).toBeInTheDocument()

//         const expectedStratum = screen.getAllByText(/Stratum/i)
//         expect(expectedStratum.length).toBe(2)
//         for (const element of expectedStratum)
//             expect(element).toBeInTheDocument()
         
//         expect(screen.getByText(mockNTPData.ip)).toBeInTheDocument()
//         expect(screen.getByText(mockRIPEData.measurementData.ip)).toBeInTheDocument()
//         expect(screen.getByText(String(mockRIPEData.measurement_id))).toBeInTheDocument()
//     })

//     test('Show Not found on status code 404', () => {
//         render(<ResultSummary data={null} ripeData={mockRIPEData} 
//                               err={new Error()} httpStatus={404} errMessage={'Domain name or IP address not found'}
//                               ripeErr={null} ripeStatus={"complete"}/>)

//         expect(screen.getByText(/Error 404: Domain name or IP address not found/)).toBeInTheDocument()
//     })

//     test('Show Server Unreachable on status code 400', () => {
//         render(<ResultSummary data={null} ripeData={mockRIPEData} 
//                               err={new Error()} httpStatus={400} errMessage={'Server is not reachable'}
//                               ripeErr={null} ripeStatus={"complete"}/>)

//         expect(screen.getByText(/Error 400: Server is not reachable/)).toBeInTheDocument()
//     })

//     test('Show Rate limiting on status code 429', () => {
//         render(<ResultSummary data={null} ripeData={mockRIPEData} 
//                               err={new Error()} httpStatus={429} errMessage={'Too many requests in a short amount of time'}
//                               ripeErr={null} ripeStatus={"complete"}/>)

//         expect(screen.getByText(/Error 429: Too many requests in a short amount of time/)).toBeInTheDocument()
//     })

//     test('Show DNS unresolvable on status code 422', () => {
//         render(<ResultSummary data={null} ripeData={mockRIPEData} 
//                               err={new Error()} httpStatus={422} errMessage={'Domain name cannot be resolved'}
//                               ripeErr={null} ripeStatus={"complete"}/>)

//         expect(screen.getByText(/Error 422: Domain name cannot be resolved/)).toBeInTheDocument()
//     })

//     test('Show Internal server error on status code 500', () => {
//         render(<ResultSummary data={null} ripeData={mockRIPEData} 
//                               err={new Error()} httpStatus={500} errMessage={'Internal server error occurred'}
//                               ripeErr={null} ripeStatus={"complete"}/>)

//         expect(screen.getByText(/Error 500: Internal server error occurred/)).toBeInTheDocument()
//     })

//     test('Show Unknown error on unknown status code', () => {
//         render(<ResultSummary data={null} ripeData={mockRIPEData} 
//                               err={new Error()} httpStatus={111} errMessage={'Unknown error occurred'}
//                               ripeErr={null} ripeStatus={"complete"}/>)

//         expect(screen.getByText(/Error 111: Unknown error occurred/)).toBeInTheDocument()
//     })
//     test('Show RIPE Timeout message', () => {
//     render(<ResultSummary
//             data={mockNTPData} ripeData={null} err={null} errMessage={null}
//             httpStatus={200} ripeErr={null} ripeStatus="timeout"
//             />
//         )

//         expect(screen.getByText((content) =>
//             content.includes("RIPE Measurement timed out.")
//         )).toBeInTheDocument();
//     })

//     test('Show RIPE Failure message', () => {
//     render(<ResultSummary
//             data={mockNTPData} ripeData={null} err={null} errMessage={null}
//             httpStatus={200} ripeErr={new Error()} ripeStatus="error"
//             />
//         )

//         expect(screen.getByText(/RIPE measurement failed/)).toBeInTheDocument()
//     })

//     test('Show RIPE loading pending', () => {
//         render(<ResultSummary
//             data={mockNTPData} ripeData={null} err={null} errMessage={null}
//             httpStatus={200} ripeErr={new Error()} ripeStatus="pending"
//             />
//         )
//         expect(screen.getByRole('loading')).toBeInTheDocument()
//         expect(screen.getByRole('loading')).toHaveClass("loading-spinner")
//         expect(screen.getByRole('loading')).toHaveClass("medium")
//     })

//     test('Show RIPE loading partial', () => {
//         render(<ResultSummary
//             data={mockNTPData} ripeData={null} err={null} errMessage={null}
//             httpStatus={200} ripeErr={new Error()} ripeStatus="partial_results"
//             />
//         )
//         expect(screen.getByRole('loading')).toBeInTheDocument()
//         expect(screen.getByRole('loading')).toHaveClass("loading-spinner")
//         expect(screen.getByRole('loading')).toHaveClass("medium")
//     })

// })
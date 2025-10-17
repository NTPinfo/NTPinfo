import L, { LatLngTuple } from 'leaflet'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import { useEffect, useState, useRef } from 'react'
import { NTPData, RIPEData } from '../utils/types'
import greenProbeImg from '../assets/green-probe.png'
import yellowProbeImg from '../assets/yellow-probe.png'
import redProbeImg from '../assets/red-probe.png'
import darkRedProbeImg from '../assets/dark-red-probe.png'
import grayProbeImg from '../assets/gray-probe.png'
import ntpServerImg from '../assets/ntp-server-icon-black.png'
import vantagePointImg from '../assets/vantage-point-logo-black.png'
import unavailableNtpImg from '../assets/unavailable-ntp-server-icon.png'

import '../styles/WorldMap.css'

/**
 * Standard code added for the proper functioning of the default icon when using Leaflet with Vite
 */
delete (L.Icon.Default.prototype as { _getIconUrl?: unknown })._getIconUrl

L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  zIndexOffset: 1000
})

/**
 * Custom Icons used for markers on the map, each with a different color indicating the RTT time
 */
const greenIcon = new L.Icon({
  iconUrl: greenProbeImg,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
  popupAnchor: [0, -8]
})

const yellowIcon = new L.Icon({
  iconUrl: yellowProbeImg,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
  popupAnchor: [0, -8]
})

const redIcon = new L.Icon({
  iconUrl: redProbeImg,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
  popupAnchor: [0, -8]
})

const darkRedIcon = new L.Icon({
  iconUrl: darkRedProbeImg,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
  popupAnchor: [0, -8]
})

const grayIcon = new L.Icon({
  iconUrl: grayProbeImg,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
  popupAnchor: [0, -8]
})

/**
 * Icons for the NTP servers seen on the map.
 * The server is grayed out if there was no response from it from our server and if the probes couldn't contact it either
 */
const ntpServerIcon = new L.Icon({
  iconUrl: ntpServerImg,
  iconSize: [30, 30],
  iconAnchor: [12, 15],
  popupAnchor: [0, -8],
  zIndexOffset: 1000
})

const unavailableNtpServerIcon = new L.Icon({
  iconUrl: unavailableNtpImg,
  iconSize: [30, 30],
  iconAnchor: [12, 15],
  popupAnchor: [0, -8],
  zIndexOffset: 1000
})

/**
 * A map marker icon used to show the vantage point on the map
 */
const vantagePointIcon = new L.Icon({
  iconUrl: vantagePointImg,
  iconSize: [30, 30],
  iconAnchor: [15, 30],
  popupAnchor: [0, -28],
  zIndexOffset: 500
})

/**
 * Interface used in assigning values to the map component
 */
interface MapComponentProps {
  probes: RIPEData[] | null
  ntpServers: NTPData[] | null
  vantagePointInfo: [LatLngTuple,string] | null
  status: string | null
}

/**
 * Custom type used to save information about the different measurements received in the component
 */
type LocationInfo = {
  location: LatLngTuple
  ip: string
  server_name: string
}

/**
 * A function that sets the zoom of the map to an appropiate value depeding on how spread out all the geolocations are
 * Depends on the size of the map component on the page
 * Made to change the zoom in a responsive way with the change of the map size
 * It changes zoom when the probes update, until the user interact with the map
 * It takes into consideration only the known data points that will be shown on the map
 * @param probes the geolocation of all the probes to the shown on the map
 * @param ripeNtpServer the geolocation of all NTP servers that only the RIPE probes contacted
 * @param measurementNtpServer the geolocation all NTP servers that only our back-end measured on
 * @param intersectionNtpServers the geolocation all the NTP servers measured by both RIPE probes and our back-end
 * @param unavailableNtpServers the geolocation of all the NTP servers that the vantage point couldn't contact
 * @param vantagePoint the geolocation of the vantage point that the measurement was taken from
 */
const FitMapBounds = ({probes, ripeNtpServers, measurementNtpServers, intersectionNtpServers, unavailableNtpServers, vantagePoint}: {probes: LatLngTuple[] | null,
  ripeNtpServers: LatLngTuple[], measurementNtpServers: LatLngTuple[], intersectionNtpServers: LatLngTuple[], unavailableNtpServers: LatLngTuple[], vantagePoint: LatLngTuple | null}) => {
  const map = useMap()
  const userInteracted = useRef(false)
  const ignoreEvents = useRef(false)

  useEffect(() => {

    const onZoomOrMove = () => {
      if (ignoreEvents.current) return
      userInteracted.current = true
    }

    map.on('zoomstart', onZoomOrMove)
    map.on('dragstart', onZoomOrMove)

    return () => {
      map.off('zoomstart', onZoomOrMove)
      map.off('dragstart', onZoomOrMove)
    }
  }, [map, vantagePoint])

  useEffect(() => {
    if (userInteracted.current) return

    const fitBounds = () => {
      const allPoints = [...(probes ?? []), ...ripeNtpServers, ...measurementNtpServers, ...intersectionNtpServers, ...unavailableNtpServers, ...(vantagePoint ? [vantagePoint] : [])]

      if (allPoints.length === 0) return

      const bounds = L.latLngBounds(allPoints)
      ignoreEvents.current = true
      map.fitBounds(bounds, { padding: [15, 15] })
      setTimeout(() => {
        ignoreEvents.current = false
      }, 100)
    }

    fitBounds()

    const handleWindowResize = () => {
      requestAnimationFrame(() => {
        fitBounds()
      })
    }
    window.addEventListener('resize', handleWindowResize)
    return () => {window.removeEventListener('resize', handleWindowResize)}
  }, [map, probes, ripeNtpServers, measurementNtpServers, intersectionNtpServers, unavailableNtpServers, vantagePoint])

  return null
}

/**
 * A function to draw connecting lines on the map
 * It draws lines from each RIPE probe to the NTP server it measured
 * It also draws lines from the vantage point to every NTP server it measured
 * @param probes the geolocation of all the probes to the shown on the map
 * @param measurementNtpServer the geolocation all NTP server that only our back-end measured on
 * @param intersectionNtpServers the geolocation all the NTP servers measured by both RIPE probes and our back-end
 * @param unavailableNtpServers the geolocation of all the NTP servers that the vantage point couldn't contact
 * @param vantagePoint the geolocation of the vantage point that the measurement was taken from
 */
const DrawConnectingLines = ({probes, measurementNtpServers, intersectionNtpServers, unavailableNtpServers, vantagePoint}: {probes: RIPEData[] | null,
  measurementNtpServers: LatLngTuple[], intersectionNtpServers: LatLngTuple[], unavailableNtpServers: LatLngTuple[], vantagePoint: LatLngTuple}) => {
  const map = useMap()

  useEffect(() => {
    measurementNtpServers.map(x => {
      L.polyline([x,vantagePoint], {color:'#1961ac', opacity: 0.8, weight: 1}).addTo(map)
    })
    intersectionNtpServers.map(x => {
      L.polyline([x,vantagePoint], {color:'#1961ac', opacity: 0.8, weight: 1}).addTo(map)
    })
    unavailableNtpServers.map(x => {
      L.polyline([x,vantagePoint], {color:'#1961ac', opacity: 0.8, weight: 1}).addTo(map)
    })
    if (!vantagePoint || !probes|| probes.length === 0) return
    probes.map(x => {
      L.polyline([x.probe_location,x.measurementData.coordinates], {color: '#1961ac', opacity: 0.8, weight: 1}).addTo(map)
    })
  },[map, probes, measurementNtpServers, intersectionNtpServers, unavailableNtpServers, vantagePoint])

  return null
}

/**
 * Function to load the legend
 * It loads it once on initial load, and stops doing it on subsequent reloads
 * Shows what each possible icon on the map means
 */
const LegendControl = () => {
  const map = useMap()
  const legendRef = useRef<L.Control | null>(null)

  useEffect(() => {
    const script = document.createElement("script")
    script.src = "/leaflet-legend/leaflet.legend.js"

    const link = document.createElement("link")
    link.rel = "stylesheet"
    link.href = "/leaflet-legend/leaflet.legend.css"

    const cleanup = () => {
      if (legendRef.current) {
        map.removeControl(legendRef.current)
        legendRef.current = null
      }
      document.head.removeChild(link)
      document.body.removeChild(script)
    }

    script.onload = () => {
      if (legendRef.current) return // already added

      const legend = (L.control as unknown as { legend: (opts: object) => L.Control }).legend({
        position: "bottomleft", opacity: "0.0", symbolWidth: "30", symbolHeight: "30",
        legends: [
          { label: "  NTP Servers", type: "image", url: ntpServerImg },
          { label: "  Failing NTP Servers", type: "image", url: unavailableNtpImg },
          { label: "  Vantage Point", type: "image", url: vantagePointImg },
          { label: "  < 15 ms RTT", type: "image", url: greenProbeImg },
          { label: "  < 40 ms RTT", type: "image", url: yellowProbeImg },
          { label: "  < 150 ms RTT", type: "image", url: redProbeImg },
          { label: "  > 150 ms RTT", type: "image", url: darkRedProbeImg },
          { label: "  No Response", type: "image", url: grayProbeImg }
        ]
      })

      legend.addTo(map)
      legendRef.current = legend as L.Control
    }

    document.body.appendChild(script)
    document.head.appendChild(link)

    return cleanup
  }, [map])

  return null
}

/**
 * Function returning an icon with a specific color depeding on the RTT measured by a specific probe
 * Cutoff values set similarly to RIPE
 * @param rtt the RTT measured by a specific probe
 * @param measured boolean indicating whether the measurement was actually successful
 * @returns the specific icon which should be shown on the map for the probe
 */
const getIconByRTT = (rtt: number, measured: boolean): L.Icon => {
  if (measured == false) return grayIcon;
  if (rtt < 15) return greenIcon;
  if (rtt < 40) return yellowIcon;
  if (rtt < 150) return redIcon;
  return darkRedIcon;
}

/**
 * Function returining a string with the measurement result of the probe
 * Returns either the string of the measurenemt value or No Reply if the measurement wasn't performed
 * @param value RTT/offset value measured by the probe
 * @returns a string indicating this specific value
 */
const stringifyRTTAndOffset = (data: RIPEData): [string,string] => {
  if (data.measurementData.RTT === -1000) return ["No Reply","No Reply"]
  else return [data.measurementData.RTT.toString(),data.measurementData.offset.toString()]
}

/**
 * The function for creating the WorldMap Component
 * Shows error text in case that an error occurs in fetching RIPE Data
 * Used a base tile map offered by Carto, specifically the Dark Matter basemap
 * Shows the status of the map(loading, finished, error)
 * Each probe is shown on the map with an icon of a different color depending on the RTT measured by it
 * Besides this, the vantage point and the NTP server(s) are also shown
 * The NTP servers that are measured by both the vantage point or one of the probes are only shown once
 * This is done by looking at the location, as they could have a different IP, but be in the same location
 * Each probe has a popup which shows the following:
 *  The RIPE probe ID, with a link to its page on the RIPE Atlas website
 *  The RTT measured
 *  The offset measured
 *  The location of the probe
 * The NTP server(s) has a popup showing the following:
 *  Who measured on the server
 *  The name of the NTP server
 *  The IP of the specifc NTP server which was used
 * The vantage point has a popup that shows:
 *  The IP of the vantage point
 *  The location of the vantage point
 * The map has lines drawn in between icons to better illustract which probe and vantage point measured what server
 * The map's zoom get automatically readjusted depending on the size of the map on the page
 * Each server measured, both by the probes and the vantage point, is checked for Anycast.
 * In the case that Anycast is detected, this information is displayed to the user.
 * @param probes Data of all the measured probes, as an array of RIPEData values
 * @param ntpServers Data of all the NTP severs that the vantage point measured as an array of NTPData
 * @param vantagePointInfo The IP and location of the vantage point if received as information from the back-end
 * @param status the current status of the polling of the RIPE measurements
 * @returns a WorldMap component showing all probes, the NTP server and relevant values for all of them
 */
export default function WorldMap ({probes, ntpServers, vantagePointInfo, status}: MapComponentProps) {
  const [statusMessage, setStatusMessage] = useState<string>("")

  const [ripeOnlyLocations, setRipeOnlyLocations] = useState<LocationInfo[]>([])
  const [ntpOnlyLocations, setNtpOnlyLocations] = useState<LocationInfo[]>([])
  const [intersectedLocations, setIntersectedLocations] = useState<LocationInfo[]>([])
  const [failedLocations, setFailedLocations] = useState<LocationInfo[]>([])

  const [isAnycast, setIsAnycast] = useState<boolean>(false)

  /**
   * Effect used for categorizing the NTP servers measured into:
   * Measured by only RIPE probes
   * Measured by only the vantage point
   * Measured by both
   * NTP servers that the vantage point didnt manage to connect to
   */
  useEffect(() => {
    /**
     * Checks done in case that either RIPE or the vantage point didn't return results
     */
    if (!probes && !ntpServers) return

    if (!probes && ntpServers) {
      setRipeOnlyLocations([])
      setIntersectedLocations([])

      const ntpLocations = new Map<string, LocationInfo>()
      const failedLocations = new Map<string, LocationInfo>()

      for (const ntp of ntpServers) {
        if (!ntp || !ntp.coordinates) continue
        const locStr = ntp.coordinates.join(',')
        if (ntp.RTT === -1) {
          failedLocations.set(locStr, { location: ntp.coordinates, ip: ntp.ip, server_name: ntp.server_name })
        } else {
          ntpLocations.set(locStr, { location: ntp.coordinates, ip: ntp.ip, server_name: ntp.server_name })
        }
      }

      setNtpOnlyLocations(Array.from(ntpLocations.values()))
      setFailedLocations(Array.from(failedLocations.values()))
      return
    }

    if (!ntpServers && probes){
      setFailedLocations([])
      setNtpOnlyLocations([])
      setIntersectedLocations([])

      const ripeLocations = new Map<string, LocationInfo>()

      for (const probe of probes) {
        const ip = probe?.measurementData?.ip
        const loc = probe?.measurementData?.coordinates
        if (!ip || !loc) continue
        const locStr = loc.join(',')
        const server_name = probe?.measurementData?.server_name ?? ""
        ripeLocations.set(locStr, { location: loc, ip, server_name })
      }

      setRipeOnlyLocations(Array.from(ripeLocations.values()))
      return
    }

    //sanity check requred by React
    if (!probes || !ntpServers) return

    const probeIPMap = new Map<string, RIPEData>()

    const ripeLocations = new Map<string, LocationInfo>()
    const ntpLocations = new Map<string, LocationInfo>()
    const failedLocations = new Map<string, LocationInfo>()

    for (const probe of probes) {
      const ip = probe?.measurementData?.ip
      const loc = probe?.measurementData?.coordinates
      if (!ip || !loc) continue
      const locStr = loc.join(',')
      const server_name = probe?.measurementData?.server_name ?? ""
      probeIPMap.set(ip, probe)
      ripeLocations.set(locStr, { location: loc, ip, server_name })
    }

    const probeIps = new Set(probeIPMap.keys())
    const inMeasurements = ntpServers.filter(x => !!x && !!x.ip && !!x.coordinates && !probeIps.has(x.ip))
    const unavailable = inMeasurements.filter(x => x.RTT === -1)

    for (const ntp of ntpServers) {
      if (!ntp || !ntp.coordinates) continue
      const loc = ntp.coordinates
      const locStr = loc.join(',')
      ntpLocations.set(locStr, { location: loc, ip: ntp.ip, server_name: ntp.server_name })
    }

    for (const ntp of unavailable) {
      if (!ntp || !ntp.coordinates) continue
      const loc = ntp.coordinates
      const locStr = loc.join(',')
      if (!ripeLocations.has(locStr)) {
        failedLocations.set(locStr, { location: loc, ip: ntp.ip, server_name: ntp.server_name })
      }
    }

    const intersected = new Map<string, LocationInfo>()
    const ripeOnly = new Map<string, LocationInfo>()
    const ntpOnly = new Map<string, LocationInfo>()

    for (const [locStr, info] of ripeLocations) {
      if (ntpLocations.has(locStr)) {
        intersected.set(locStr, info)
      } else {
        ripeOnly.set(locStr, info)
      }
    }

    for (const [locStr, info] of ntpLocations) {
      if (!ripeLocations.has(locStr)) {
        ntpOnly.set(locStr, info)
      }
    }

    setRipeOnlyLocations(Array.from(ripeOnly.values()))
    setNtpOnlyLocations(Array.from(ntpOnly.values()))
    setIntersectedLocations(Array.from(intersected.values()))
    setFailedLocations(Array.from(failedLocations.values()))
  }, [probes,ntpServers])

  /**
   * Effect to check if the NTP servers used use anycast, which would lead to less accurate geolocation data
   */
  useEffect(() => {
    if (!probes || !ntpServers) return

    setIsAnycast(probes.some(x => x.measurementData.is_anycast === true) || ntpServers.some(x => x.is_anycast === true))
  }, [probes, ntpServers])

  /**
   * Effect to dynamically update the status shown depening on the progress of the RIPE measurement
   */
  useEffect(() => {
    if (status === "pending"){
      setRipeOnlyLocations([])
      setNtpOnlyLocations([])
      setIntersectedLocations([])
      setFailedLocations([])
      return
    } else if (status === "partial_results"){
      setStatusMessage("Map Loading...")
    } else if(status === "complete" || status === "timeout") {
      setStatusMessage("Map Fully Loaded")
    } else if (status === "error") {
      setStatusMessage("Error loading RIPE data")
    }
    }, [probes, status])

  const probe_locations = probes?.map(x => x.probe_location) ?? []
  const icons = probes?.map(x => getIconByRTT(x.measurementData.RTT, x.got_results)) ?? []
    return (
      <div className='map-container' style={{height: '500px', width: '100%', padding: '10px'}}>
        <h2>{statusMessage}</h2>
        {isAnycast && <h2>This server uses Anycast. Server Geolocation might be inaccurate</h2>}
        <MapContainer style={{height: '100%', width: '100%'}}>
            <TileLayer
                url = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                attribution= '&copy; <a href="https://carto.com/">CARTO</a>'
                subdomains={['a', 'b', 'c', 'd']}
                maxZoom={19}
            />

            {probes && (
            <>
              {probe_locations.map((pos, index) => (<Marker key = {index} position = {pos} icon = {icons[index]}>
                <Popup>
                  Probe ID: <a href = {`https://atlas.ripe.net/probes/${probes[index].probe_id}/overview`} target='_blank' rel="noopener noreferrer">{probes[index].probe_id}</a><br/>
                  Offset: {stringifyRTTAndOffset(probes[index])[1]}ms<br/>
                  RTT: {stringifyRTTAndOffset(probes[index])[0]}ms<br/>
                  Location: {pos[0]}, {pos[1]}
                </Popup>
              </Marker>))}
              </>)}

              {ripeOnlyLocations.map((x,index) => (
                <Marker key={index} position={x.location} icon={ntpServerIcon}>
                  <Popup>
                    NTP Server (RIPE)<br/>
                    IP: {x.ip}<br/>
                    Name: {x.server_name}<br/>
                    Location: {x.location[0]}, {x.location[1]}
                  </Popup>
                </Marker>
              ))}

              {ntpOnlyLocations.map((x,index) => (
                <Marker key={index} position={x.location} icon={ntpServerIcon}>
                  <Popup>
                    NTP Server (Vantage Point)<br/>
                    IP: {x.ip}<br/>
                    Name: {x.server_name}<br/>
                    Location: {x.location[0]}, {x.location[1]}
                  </Popup>
                </Marker>
              ))}

              {intersectedLocations.map((x,index) => (
                <Marker key={index} position={x.location} icon={ntpServerIcon}>
                  <Popup>
                    NTP Server<br/>
                    IP: {x.ip}<br/>
                    Name: {x.server_name}<br/>
                    Location: {x.location[0]}, {x.location[1]}
                  </Popup>
                </Marker>
              ))}

              {failedLocations.map((x,index) => (
                <Marker key={index} position={x.location} icon={unavailableNtpServerIcon}>
                  <Popup>
                    NTP Server (Unavailable)<br/>
                    IP: {x.ip}<br/>
                    Name: {x.server_name}<br/>
                    Location: {x.location[0]}, {x.location[1]}
                  </Popup>
                </Marker>
              ))}

              <FitMapBounds probes={probe_locations} ripeNtpServers={ripeOnlyLocations.map(x=>x.location)} measurementNtpServers = {ntpOnlyLocations.map(x=>x.location)}
                  intersectionNtpServers={intersectedLocations.map(x=>x.location)} unavailableNtpServers={failedLocations.map(x=>x.location)}
                  vantagePoint={vantagePointInfo?.[0] ?? null}/>
              <LegendControl/>
              {vantagePointInfo &&
              <>
                <Marker position = {vantagePointInfo[0]} icon = {vantagePointIcon}>
                    <Popup>
                      Vantage Point<br/>
                      IP: {vantagePointInfo[1]}<br/>
                      Location: {vantagePointInfo[0][0]}, {vantagePointInfo[0][1]}
                    </Popup>
                </Marker>
                <DrawConnectingLines probes={probes} measurementNtpServers = {ntpOnlyLocations.map(x=>x.location)}
                  intersectionNtpServers={intersectedLocations.map(x=>x.location)} unavailableNtpServers={failedLocations.map(x=>x.location)}
                  vantagePoint={vantagePointInfo[0]}/>
              </>}
        </MapContainer>
        <div style={{height:'20px'}}></div>
      </div>
    )
}
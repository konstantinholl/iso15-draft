import 'maplibre-gl/dist/maplibre-gl.css'

import maplibregl, { type MapMouseEvent, type Map as MapLibreMap } from 'maplibre-gl'
import { useEffect, useRef } from 'react'

export type TravelMode = 'pedestrian' | 'bicycle'

export type InspectorResponse = {
  latitude: number
  longitude: number
  travel_mode: TravelMode
  is_15_min_compliant: boolean
  bottleneck_category: string | null
  categories: Record<
    string,
    {
      amenity_id: number
      duration_seconds: number
      duration_minutes: number
      distance_meters: number
    }
  >
  missing_categories: string[]
  bottleneck_route: {
    type: 'LineString'
    coordinates: [number, number][]
  } | null
}

type AccessibilityMapProps = {
  travelMode: TravelMode
  onInspect: (latitude: number, longitude: number) => void
  inspection: InspectorResponse | null
}

const TUEBINGEN: [number, number] = [9.0576, 48.5216]

export function AccessibilityMap({ travelMode, onInspect, inspection }: AccessibilityMapProps): JSX.Element {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<MapLibreMap | null>(null)
  const marker = useRef<maplibregl.Marker | null>(null)
  const onInspectRef = useRef(onInspect)
  onInspectRef.current = onInspect

  useEffect(() => {
    if (!mapContainer.current) return

    const mapInstance = new maplibregl.Map({
      container: mapContainer.current,
      center: TUEBINGEN,
      zoom: 13,
      style: {
        version: 8,
        sources: {
          osm: {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors',
          },
        },
        layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
      },
    })

    const handleClick = (event: MapMouseEvent) => {
      onInspectRef.current(event.lngLat.lat, event.lngLat.lng)
    }
    mapInstance.on('click', handleClick)
    map.current = mapInstance

    return () => {
      mapInstance.remove()
      map.current = null
    }
  }, [])

  useEffect(() => {
    if (!map.current || !inspection) return

    marker.current?.remove()
    marker.current = new maplibregl.Marker({ color: '#d94f4f' })
      .setLngLat([inspection.longitude, inspection.latitude])
      .addTo(map.current)

    const routeSource = map.current.getSource('bottleneck-route') as maplibregl.GeoJSONSource | undefined
    if (inspection.bottleneck_route) {
      const data = {
        type: 'Feature',
        properties: {},
        geometry: inspection.bottleneck_route,
      } as const
      if (routeSource) {
        routeSource.setData(data)
      } else {
        map.current.addSource('bottleneck-route', { type: 'geojson', data })
        map.current.addLayer({
          id: 'bottleneck-route',
          type: 'line',
          source: 'bottleneck-route',
          paint: { 'line-color': '#d94f4f', 'line-width': 4 },
        })
      }
    } else if (routeSource) {
      routeSource.setData({ type: 'FeatureCollection', features: [] })
    }
  }, [inspection])

  return <div ref={mapContainer} className="map-container" aria-label={`Accessibility map, ${travelMode} mode`} />
}

import { useState } from 'react'
import { AccessibilityMap, type InspectorResponse, type TravelMode } from './components/AccessibilityMap'

export function App(): JSX.Element {
  const [travelMode, setTravelMode] = useState<TravelMode>('pedestrian')
  const [inspection, setInspection] = useState<InspectorResponse | null>(null)
  const [selectedCoordinates, setSelectedCoordinates] = useState<[number, number] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function inspectPoint(latitude: number, longitude: number): Promise<void> {
    setSelectedCoordinates([latitude, longitude])
    setInspection(null)
    setError(null)
    setLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/v1/inspector/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ latitude, longitude, travel_mode: travelMode }),
      })
      const body = await response.json().catch(() => null) as
        | InspectorResponse
        | { detail?: { message?: string } }
        | null
      if (!response.ok) {
        const detail =
          body && 'detail' in body && body.detail?.message
            ? body.detail.message
            : `Inspection failed (HTTP ${response.status}).`
        throw new Error(detail)
      }
      if (!body || !('categories' in body)) {
        throw new Error('The inspection response was invalid.')
      }
      setInspection(body)
    } catch (inspectionError) {
      setError(inspectionError instanceof Error ? inspectionError.message : 'Inspection failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main>
      <h1>15-Minute City Accessibility Studio</h1>
      <p className="intro">Click anywhere on the map to inspect access to essential amenities.</p>
      <div className="toolbar">
        <label htmlFor="travel-mode">Travel mode</label>
        <select
          id="travel-mode"
          value={travelMode}
          onChange={(event) => setTravelMode(event.target.value as TravelMode)}
        >
          <option value="pedestrian">Walking</option>
          <option value="bicycle">Cycling</option>
        </select>
      </div>
      <div className="workspace">
        <AccessibilityMap travelMode={travelMode} onInspect={inspectPoint} inspection={inspection} />
        <aside className="results" aria-live="polite">
          {!selectedCoordinates && <p className="muted">Drop a pin on the map to see accessibility results.</p>}
          {selectedCoordinates && loading && <p>Calculating accessibility…</p>}
          {error && <p className="error">{error}</p>}
          {inspection && (
            <>
              <h2>{inspection.is_15_min_compliant ? 'Within 15 minutes' : 'Outside 15 minutes'}</h2>
              <p className={inspection.is_15_min_compliant ? 'status good' : 'status warning'}>
                {inspection.is_15_min_compliant
                  ? 'All available essential categories are reachable.'
                  : `Bottleneck: ${inspection.bottleneck_category ?? 'unavailable'}`}
              </p>
              <dl>
                {Object.entries(inspection.categories).map(([category, result]) => (
                  <div className="metric" key={category}>
                    <dt>{category.replace(/_/g, ' ')}</dt>
                    <dd>{result.duration_minutes.toFixed(1)} min</dd>
                  </div>
                ))}
              </dl>
              {inspection.missing_categories.length > 0 && (
                <p className="muted">Missing data: {inspection.missing_categories.join(', ')}</p>
              )}
            </>
          )}
        </aside>
      </div>
    </main>
  )
}

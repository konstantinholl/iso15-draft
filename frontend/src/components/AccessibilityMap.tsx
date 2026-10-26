import type { FeatureCollection } from 'geojson'
import { useMemo } from 'react'

/**
 * Map scaffold ready to host deck.gl H3HexagonLayer + MapLibre base map integration.
 * The initial skeleton intentionally renders a simple development placeholder.
 */
export function AccessibilityMap(): JSX.Element {
  const emptyGeoJson = useMemo<FeatureCollection>(() => ({ type: 'FeatureCollection', features: [] }), [])

  return (
    <section>
      <p>Map shell initialized. Integrate MapLibre and H3HexagonLayer in feature branches.</p>
      <pre>{JSON.stringify(emptyGeoJson, null, 2)}</pre>
    </section>
  )
}

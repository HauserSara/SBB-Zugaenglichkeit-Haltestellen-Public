import { Component, OnInit, OnDestroy, AfterViewInit } from '@angular/core';
import maplibregl, { Map, Marker, LngLat, GeoJSONSource, AttributionControl } from 'maplibre-gl';
import { HttpClient } from '@angular/common/http';
import { Feature, Geometry } from 'geojson';

declare global {
  interface Window { JM_API_KEY: string }
}

@Component({
  selector: 'map-nav',
  templateUrl: './map-nav.component.html',
  styleUrls: ['./map-nav.component.css']
})
export class MapNav implements OnInit, OnDestroy, AfterViewInit {
  apiKey = window.JM_API_KEY;
  private map!: Map;
  public markers: Marker[] = [];
  
  constructor(private http: HttpClient) { }
  
  ngOnInit(): void {
    
  }

  ngAfterViewInit(): void {
    this.initializeMap();
    this.map.resize()
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
    }
    this.clearMarkers();
  }

  private initializeMap(): void {
    if (this.map) {
      this.map.remove();  // Clean up the existing map before creating a new one
    }

    this.map = new Map({
      container: 'map-nav', // container ID
      style: `https://journey-maps-tiles.geocdn.sbb.ch/styles/base_bright_v2/style.json?api_key=${this.apiKey}`, // your MapTiler style URL
      center: [8.2275, 46.8182], // starting position [lng, lat]
      zoom: 7.5, // starting zoom
      attributionControl: false
    });

    this.map.on('load', () => {
      this.map.on('click', (e) => {
        this.handleMapClick(e.lngLat);
      });
    });

    const attributionControl = new AttributionControl({
      compact: true
    });
    this.map.addControl(attributionControl, 'top-left');
  }

  private handleMapClick(lngLat: LngLat): void {
    if (this.markers.length >= 2) {
      this.clearMarkers();
    }

    this.addMarker(lngLat);

    if (this.markers.length === 2) {
      this.getRoute();
    }
  }

  addMarker(lngLat: LngLat): void {
    const el = document.createElement('div');
    el.className = 'marker';
    el.style.backgroundImage = 'url(assets/icons/location-pin.svg)';
    el.style.width = '60px';
    el.style.height = '60px';
    el.style.backgroundSize = 'cover';

    const marker = new Marker({ element: el, anchor: 'bottom' }).setLngLat(lngLat).addTo(this.map);
    this.markers.push(marker);
  }

  getRoute(): void {
    if (this.markers.length < 2) {
      return; // Ensure there are exactly two markers
    }

    const url = 'http://127.0.0.1:8000/route_ojp/';
    const body = {
      "lat1": this.markers[0].getLngLat().lat,
      "lon1": this.markers[0].getLngLat().lng,
      "lat2": this.markers[1].getLngLat().lat,
      "lon2": this.markers[1].getLngLat().lng,
      "time": "12:00"
    };
    const headers = {
      'Content-Type': 'application/json',
      'User-Agent': 'sbb-a11y-app'
    };
    console.log(`Sending POST request to ${url} with body:`, body);

    this.http.post<any>(url, body, { headers }).subscribe({
      next: (geojsonData) => this.displayGeoJSON(geojsonData),
      error: (error) => console.error("POST call in error", error.error),
      complete: () => console.log("The POST observable is now completed.")
    });
  }

  displayGeoJSON(geoJSONData: any) {
    const layerColor = '#FF0000'; // Define a constant color for all layers

    Object.keys(geoJSONData).forEach((routeKey) => {
      const route = geoJSONData[routeKey];

      Object.keys(route).forEach((legKey, index) => {
        const leg = route[legKey];

        if (leg.type === 'ContinuousLeg' && leg.coordinates.length > 0) {
          // Ensure coordinates are unique and the polyline is not closed
          const uniqueCoordinates = leg.coordinates.map((coord: number[]) => ([coord[1], coord[0]] as [number, number]));
          const filteredCoordinates = uniqueCoordinates.filter((coord: [number, number], index: number, self: [number, number][]) =>
            index === self.findIndex((c: [number, number]) => c[0] === coord[0] && c[1] === coord[1])
          );

          const geojsonData: Feature<Geometry> = {
            type: 'Feature',
            geometry: {
              type: 'LineString',
              coordinates: filteredCoordinates
            },
            properties: {}  // Add empty properties object
          };

          const sourceId = `route-${routeKey}-${legKey}`;
          const layerId = `route-layer-${routeKey}-${legKey}`;

          if (!this.map.getSource(sourceId)) {
            this.map.addSource(sourceId, {
              type: 'geojson',
              data: geojsonData
            });

            this.map.addLayer({
              id: layerId,
              type: 'line',
              source: sourceId,
              layout: {},
              paint: {
                'line-color': layerColor,
                'line-width': 5
              }
            });
          } else {
            // Update the source data if it already exists
            (this.map.getSource(sourceId) as GeoJSONSource).setData(geojsonData);
          }

          // Zoom to the bounding box of the first feature if it's the first leg
          if (index === 0) {
            const bounds = filteredCoordinates.reduce((bounds: maplibregl.LngLatBounds, coord: [number, number]) => bounds.extend(coord), new maplibregl.LngLatBounds(filteredCoordinates[0], filteredCoordinates[0]));
            this.map.fitBounds(bounds, { padding: 20 });
          }
        }
      });
    });
  }

  clearRoutes(): void {
    if (this.map && this.map.getStyle()) {
      this.map.getStyle().layers.forEach(layer => {
        if (layer.id.startsWith('route-layer-') && this.map.getLayer(layer.id)) {
          this.map.removeLayer(layer.id);
        }
      });
      Object.keys(this.map.getStyle().sources).forEach(sourceId => {
        if (sourceId.startsWith('route-') && this.map.getSource(sourceId)) {
          this.map.removeSource(sourceId);
        }
      });
    }
  }

  clearMarkers(): void {
    this.markers.forEach(marker => marker.remove());
    this.markers = [];
    this.clearRoutes();
  }
}

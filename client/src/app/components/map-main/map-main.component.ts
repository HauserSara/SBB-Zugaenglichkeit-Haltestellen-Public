import { Component, OnDestroy, AfterViewInit, OnInit } from '@angular/core';
import { Map, Popup, GeoJSONSource, AttributionControl } from 'maplibre-gl';
import { SloidService } from '../../services/sloid.service';
import { Feature, Point, GeoJsonProperties } from 'geojson'; // Import necessary GeoJSON types

declare global {
  interface Window { JM_API_KEY: string; }
}

interface LayerProperties {
  [key: string]: 'boolean' | 'text';
}

interface Connection {
  start: string;
  end: string;
  info: string;  // Add more fields as needed
}

@Component({
  selector: 'map-main',
  templateUrl: './map-main.component.html',
  styleUrls: ['./map-main.component.css']
})
export class MapMain implements OnDestroy, AfterViewInit, OnInit {
  apiKey = window.JM_API_KEY;
  private map!: Map;
  isChecked: boolean = false;
  private validSLOIDValues: string[] = [];

  private firstClickedPoint: string | null = null;
  private secondClickedPoint: string | null = null;
  private connections: Connection[] = [];  // Store connection information
  private popup: Popup | null = null;      // Store the popup

  constructor(private sloidService: SloidService) { }

  ngOnInit() {}

  checkSloid(sloid: string): void {
    this.sloidService.getSloids(sloid).subscribe({
      next: (data) => {
        console.log('Erhaltene SLOIDs:', data);
        this.updateSLOIDFilter(data.sloids);  // Assuming data.sloids contains the list of connected SLOIDs
        this.connections = data.connections;  // Assuming data.connections contains connection information
      },
      error: (error) => console.error('Fehler beim Abrufen der SLOIDs:', error)
    });
  }

  ngAfterViewInit(): void {
    this.initializeMap();
    this.map.resize()
  }

  onToggleChange(isChecked: boolean): void {
    this.isChecked = isChecked;
    this.updateMode();
  }

  updateMode(): void {
    if (this.isChecked) {
      this.setupConnectionMode();
    } else {
      this.setupInformationMode();
    }
  }

  setupInformationMode(): void {
    console.log('Information mode activated');
    this.removeAllLayers();
    this.addGeoJsonLayer();
  }

  setupConnectionMode(): void {
    console.log('Connection mode activated');
    this.removeAllLayers();
    this.addAllPointsLayer();
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
    }
  }

  private initializeMap(): void {
    this.map = new Map({
      container: 'map-main',
      style: `https://journey-maps-tiles.geocdn.sbb.ch/styles/base_bright_v2/style.json?api_key=${this.apiKey}`,
      center: [7.56, 46.85],
      zoom: 10,
      attributionControl: false
    });

    const attributionControl = new AttributionControl({
      compact: true
    });
    this.map.addControl(attributionControl, 'top-left');

    this.map.on('load', () => {
      const icons = {
        'toilet-icon': 'assets/icons/Toiletten.svg',
        'parking-icon': 'assets/icons/Parkplatz.svg',
        'info-desk-icon': 'assets/icons/Informationsdesk.svg',
        'ticket-counter-icon': 'assets/icons/Ticket.svg',
        'reference-point-icon': 'assets/icons/Referenzpunkt.svg',
        'point': 'assets/icons/Punkt.svg',
        'Bus': 'assets/icons/Bus.svg',
        'Tram': 'assets/icons/Tram.svg',
        'Zug': 'assets/icons/Zug.svg'
      };

      Object.entries(icons).forEach(([key, src]) => {
        const image = new Image(200, 200);
        image.onload = () => this.map.addImage(key, image);
        image.src = src;
      });

      this.initializeSource();
      this.setupInformationMode();
    });
  }

  private initializeSource(): void {
    const sources = {
      'prm_toilets': 'assets/geojson/prm_toilets.geojson',
      'prm_parking_lots': 'assets/geojson/prm_parking_lots.geojson',
      'prm_info_desks': 'assets/geojson/prm_info_desks.geojson',
      'prm_ticket_counters': 'assets/geojson/prm_ticket_counters.geojson',
      'all_points': 'assets/geojson/all_points.geojson',
      'betriebspunkte_perimeter': 'assets/geojson/Betriebspunkte_Perimeter.geojson', // New dataset
      'haltekanten_perimeter': 'assets/geojson/Haltekanten_Perimeter.geojson' // New dataset
    };

    Promise.all(
      Object.entries(sources).map(([key, url]) =>
        fetch(url)
          .then(res => {
            if (!res.ok) throw new Error(`Network response was not ok for ${key}`);
            return res.json();
          })
          .then(data => {
            if (!this.map.getSource(key)) {
              this.map.addSource(key, {
                type: 'geojson',
                data: data
              });
            }
          })
      )
    ).then(() => {
      this.setupInformationMode();
    }).catch(error => console.error("Error loading the GeoJSON: ", error));
  }

  private addAllPointsLayer(): void {
    if (!this.map.getLayer('other_points-layer') && this.map.getSource('all_points')) {
      this.map.addLayer({
        id: 'other_points-layer',
        type: 'symbol',
        source: 'all_points',
        filter: ['!=', ['get', 'Bezeichnung'], 'Referenzpunkt'],
        minzoom: 13, // Only show other points at a certain zoom level
        layout: {
          'icon-image': 'point', // Default to circle if not a reference point
          'icon-size': 0.18, // Default size for other points
          "icon-anchor": "bottom"
        }
      });
    }

    if (!this.map.getLayer('reference_points-layer') && this.map.getSource('all_points')) {
      this.map.addLayer({
        id: 'reference_points-layer',
        type: 'symbol',
        source: 'all_points',
        filter: ['==', ['get', 'Bezeichnung'], 'Referenzpunkt'],
        layout: {
          'icon-image': 'reference-point-icon', // Use the reference point icon
          'icon-size': 0.2, // Size for the reference point icon
          "icon-anchor": "bottom"
        }
      });
    }

    this.setupClickHandlerForFilter();
  }
  
  private addGeoJsonLayer(): void {
    const layers: { [id: string]: { source: string, icon: string, properties: LayerProperties, maxzoom?: number } } = {
      'haltekanten_perimeter-layer': {
        source: 'haltekanten_perimeter',
        icon: 'point', // Use appropriate icon
        properties: {
          'Bezeichnung': 'text',
          'levelAccessWheelchair': 'text',
          'boardingDevice': 'text',
          'adviceAccessInfo': 'text',
          'height': 'text',
          'vehicleAccess': 'text',
          'additionalInformation': 'text'
        }
      },
      'prm_toilets-layer': {
        source: 'prm_toilets',
        icon: 'toilet-icon',
        properties: { 'WHEELCHAIR_TOILET': 'boolean' }
      },
      'prm_parking_lots-layer': {
        source: 'prm_parking_lots',
        icon: 'parking-icon',
        properties: { 'INFO': 'text', 'PRM_PLACES_AVAILABLE': 'boolean' }
      },
      'prm_info_desks-layer': {
        source: 'prm_info_desks',
        icon: 'info-desk-icon',
        properties: { 'INDUCTION_LOOP': 'boolean', 'OPEN_HOURS': 'text', 'WHEELCHAIR_ACCESS': 'boolean' }
      },
      'prm_ticket_counters-layer': {
        source: 'prm_ticket_counters',
        icon: 'ticket-counter-icon',
        properties: { 'DESCRIPTION': 'text', 'WHEELCHAIR_ACCESS': 'boolean' }
      },
      'betriebspunkte_perimeter-layer': {
        source: 'betriebspunkte_perimeter',
        icon: 'point', // Default icon, will be overridden by expression
        properties: {
          'Verkehrsmittel_Bezeichnung': 'text',
          'assistanceAvailability': 'text',
          'alternativeTransportCondition': 'text',
          'assistanceCondition': 'text',
          'freeText': 'text',
          'wheelchairTicketMachine': 'text',
          'assistanceRequestFulfilled': 'text',
          'Name': 'text' // Add the 'Name' attribute
        },
        maxzoom: 16 // Set the maximum zoom level for this layer
      }
    };
  
    Object.entries(layers).forEach(([id, { source, icon, properties, maxzoom }]) => {
      if (this.map.getSource(source) && !this.map.getLayer(id)) {
        const layout: any = {
          'icon-image': icon,
          'icon-size': 0.1,
          'visibility': 'visible'
        };
  
        // Use expression for icon-image and text-field in the respective layers
        if (id === 'betriebspunkte_perimeter-layer') {
          layout['icon-image'] = ['get', 'Verkehrsmittel_Bezeichnung'];
          layout['text-field'] = ['get', 'Name']; // Display the 'Name' attribute
          layout['text-offset'] = [0, 1.5]; // Adjust the offset as needed
          layout['text-anchor'] = 'top'; // Position the text above the icon
          layout['text-size'] = 12; // Set the text size
        } else if (id === 'haltekanten_perimeter-layer') {
          layout['text-field'] = ['get', 'Bezeichnung']; // Display the 'Bezeichnung' attribute
          layout['text-offset'] = [0, 1.5]; // Adjust the offset as needed
          layout['text-anchor'] = 'top'; // Position the text above the icon
          layout['text-size'] = 12; // Set the text size
        }
  
        const layerConfig: any = {
          id: id,
          type: 'symbol',
          source: source,
          layout: layout
        };
  
        if (maxzoom !== undefined) {
          layerConfig.maxzoom = maxzoom;
        }
  
        this.map.addLayer(layerConfig);
  
        this.setupLayerClickHandler(id, properties);
      }
    });
  }
  
  private translateAttribute(value: string): string {
    const translations: { [key: string]: string } = {
      'YES': 'Ja',
      'NO': 'Nein',
      'NOT_APPLICABLE': 'Nicht verfügbar',
      'PLATFORM_ACCESS_WITH_ASSISTANCE': 'Plattformzugang mit Assistenz',
      'PLATFORM_NOT_WHEELCHAIR_ACCESSIBLE': 'Plattform nicht rollstuhlgerecht',
      'PLATFORM_ACCESS_WITHOUT_ASSISTANCE': 'Plattformzugang ohne Assistenz',
      'LIFTS': 'Hublift'
    };
  
    return translations[value] || value;
  }
  
  private setupLayerClickHandler(layerId: string, propertiesToShow: { [key: string]: 'boolean' | 'text' }): void {
    this.map.on('click', layerId, (e) => {
      if (e.features && e.features.length > 0) {
        const feature = e.features[0];
        if (feature.geometry.type === 'Point' && feature.geometry.coordinates.length === 2) {
          const coordinates: [number, number] = [feature.geometry.coordinates[0], feature.geometry.coordinates[1]];
          let popupContent = '<div style="font-size: 12px;">';
  
          if (layerId === 'betriebspunkte_perimeter-layer') {
            const attributesToDisplay = {
              'assistanceAvailability': 'Assistenzverfügbarkeit',
              'alternativeTransportCondition': 'Bedingungen für alternativen Transport',
              'assistanceCondition': 'Bedingungen für Assistenz',
              'freeText': 'Freitext',
              'wheelchairTicketMachine': 'Rollstuhlticketautomat',
              'assistanceRequestFulfilled': 'Assistenzanforderung erfüllt'
            };
  
            Object.entries(attributesToDisplay).forEach(([prop, translatedProp]) => {
              let propValue = feature.properties[prop];
              if (['YES', 'NO', 'NOT_APPLICABLE'].includes(propValue)) {
                propValue = this.translateAttribute(propValue);
              }
              popupContent += `<strong>${translatedProp}:</strong> ${propValue}<br>`;
            });
          } else if (layerId === 'haltekanten_perimeter-layer') {
            const bezeichnung = feature.properties['Bezeichnung'] as string;
            if (bezeichnung.startsWith('Gleis')) {
              const attributesToDisplay = {
                'levelAccessWheelchair': 'Rollstuhlgerechter Zugang',
                'boardingDevice': 'Einstiegshilfe',
                'adviceAccessInfo': 'Zugangsinformationen'
              };
  
              Object.entries(attributesToDisplay).forEach(([prop, translatedProp]) => {
                let propValue = feature.properties[prop];
                if (['YES', 'NO', 'NOT_APPLICABLE', 'LIFTS'].includes(propValue)) {
                  propValue = this.translateAttribute(propValue);
                }
                popupContent += `<strong>${translatedProp}:</strong> ${propValue}<br>`;
              });
            } else if (bezeichnung.startsWith('Kante')) {
              const attributesToDisplay = {
                'height': 'Höhe der Rollstuhleinfahrtsfläche (cm)',
                'vehicleAccess': 'Rollstuhlzugänglichkeit',
                'additionalInformation': 'Zusätzliche Informationen'
              };
  
              Object.entries(attributesToDisplay).forEach(([prop, translatedProp]) => {
                let propValue = feature.properties[prop];
                if (['PLATFORM_ACCESS_WITH_ASSISTANCE', 'PLATFORM_NOT_WHEELCHAIR_ACCESSIBLE', 'PLATFORM_ACCESS_WITHOUT_ASSISTANCE'].includes(propValue)) {
                  propValue = this.translateAttribute(propValue);
                }
                popupContent += `<strong>${translatedProp}:</strong> ${propValue}<br>`;
              });
            }
          } else {
            Object.entries(propertiesToShow).forEach(([prop, type]) => {
              let propValue = feature.properties[prop];
              let translatedProp = this.attributeTranslations[prop] || prop;
              if (type === 'boolean') {
                propValue = propValue === 1 ? 'Ja' : (propValue === 2 ? 'Nein' : 'Unbekannt');
              }
              popupContent += `<strong>${translatedProp}:</strong> ${propValue}<br>`;
            });
          }
  
          popupContent += '</div>';
  
          new Popup()
            .setLngLat(coordinates)
            .setHTML(popupContent)
            .addTo(this.map);
        }
      }
    });
  }
  
  private setupClickHandlerForFilter(): void {
    ['reference_points-layer', 'other_points-layer'].forEach(layerId => {
      this.map.on('click', layerId, (e) => {
        if (e.features && e.features.length > 0) {
          const clickedSLOID = e.features[0].properties['SLOID'];
          if (this.firstClickedPoint && !this.secondClickedPoint) {
            // If the first point is already clicked and this is the second point
            this.secondClickedPoint = clickedSLOID;
            this.displayConnectionInfo();
            this.drawConnectionLine();
          } else {
            // If this is the first point clicked
            this.firstClickedPoint = clickedSLOID;
            this.checkSloid(clickedSLOID);  // Load connected points
          }
        }
      });
    });
  }
  
  private displayConnectionInfo(): void {
    if (this.firstClickedPoint && this.secondClickedPoint) {
      const connection = this.connections.find(
        conn => (conn.start === this.firstClickedPoint && conn.end === this.secondClickedPoint) ||
                (conn.start === this.secondClickedPoint && conn.end === this.firstClickedPoint)
      );
      if (connection) {
        const coordinates = this.getMidpointCoordinates(this.firstClickedPoint, this.secondClickedPoint);
        if (coordinates) {
          const formattedInfo = connection.info.split(',').map(info => {
            const [key, value] = info.split(':').map(part => part.trim());
            return `<strong>${key}</strong>: ${value}`;
          }).join('<br>');
  
          this.popup = new Popup()
            .setLngLat(coordinates)
            .setHTML(`<p style="text-decoration: underline;">Connection Info</p>${formattedInfo}`)
            .addTo(this.map);
  
          this.popup.on('close', () => {
            this.resetConnection();
            this.resetFilter();
          });
        }
      } else {
        console.log('No connection info available.');
      }
    }
  }
  
  private drawConnectionLine(): void {
    if (this.firstClickedPoint && this.secondClickedPoint) {
      const firstPoint = this.map.querySourceFeatures('all_points', {
        filter: ['==', 'SLOID', this.firstClickedPoint]
      }).find(f => f.geometry.type === 'Point') as Feature<Point>;
  
      const secondPoint = this.map.querySourceFeatures('all_points', {
        filter: ['==', 'SLOID', this.secondClickedPoint]
      }).find(f => f.geometry.type === 'Point') as Feature<Point>;
  
      if (firstPoint && secondPoint) {
        const coordinates = [
          firstPoint.geometry.coordinates,
          secondPoint.geometry.coordinates
        ];
  
        const connectionDescription = this.getConnectionDescription(this.firstClickedPoint, this.secondClickedPoint);
  
        if (!this.map.getSource('connection-line')) {
          this.map.addSource('connection-line', {
            type: 'geojson',
            data: {
              type: 'Feature',
              geometry: {
                type: 'LineString',
                coordinates: coordinates
              },
              properties: {
                description: connectionDescription
              }
            }
          });
  
          this.map.addLayer({
            id: 'connection-line',
            type: 'line',
            source: 'connection-line',
            paint: {
              'line-color': 'red',
              'line-width': 2
            }
          });
  
          this.map.addLayer({
            id: 'connection-label',
            type: 'symbol',
            source: 'connection-line',
            layout: {
              'symbol-placement': 'line-center',
              'text-field': ['get', 'description'],
              'text-size': 12
            },
            paint: {
              'text-color': '#000'
            }
          });
        } else {
          (this.map.getSource('connection-line') as GeoJSONSource).setData({
            type: 'Feature',
            geometry: {
              type: 'LineString',
              coordinates: coordinates
            },
            properties: {
              description: connectionDescription
            }
          });
        }
      }
    }
  }
  
  private getConnectionDescription(start: string, end: string): string | null {
    const connection = this.connections.find(
      conn => (conn.start === start && conn.end === end) ||
              (conn.start === end && conn.end === start)
    );
    return connection ? connection.info : null;
  }
  
  private getMidpointCoordinates(startSLOID: string, endSLOID: string): [number, number] | null {
    const startPoint = this.map.querySourceFeatures('all_points', {
      filter: ['==', 'SLOID', startSLOID]
    }).find(f => f.geometry.type === 'Point') as Feature<Point>;
  
    const endPoint = this.map.querySourceFeatures('all_points', {
      filter: ['==', 'SLOID', endSLOID]
    }).find(f => f.geometry.type === 'Point') as Feature<Point>;
  
    if (startPoint && endPoint) {
      const [startLng, startLat] = startPoint.geometry.coordinates;
      const [endLng, endLat] = endPoint.geometry.coordinates;
      const midLng = (startLng + endLng) / 2;
      const midLat = (startLat + endLat) / 2;
      return [midLng, midLat];
    }
  
    return null;
  }
  
  public resetFilter(): void {
    if (this.map.getLayer('all_points-layer')) {
      this.map.setFilter('all_points-layer', null);
    }
  }
  
  public updateSLOIDFilter(newValues: string[]): void {
    this.validSLOIDValues = newValues;
    if (this.map.getLayer('all_points-layer')) {
      this.map.setFilter('all_points-layer', ['in', ['get', 'SLOID'], ['literal', this.validSLOIDValues]]);
    }
  }
  
  private removeAllLayers(): void {
    const layerIds = [
      'prm_toilets-layer', 
      'prm_parking_lots-layer', 
      'prm_info_desks-layer', 
      'prm_ticket_counters-layer', 
      'reference_points-layer', 
      'other_points-layer', 
      'betriebspunkte_perimeter-layer',
      'haltekanten_perimeter-layer',
      'connection-line', 
      'connection-label'
    ];
  
    layerIds.forEach(layerId => {
      if (this.map.getLayer(layerId)) {
        this.map.removeLayer(layerId);
      }
    });
  
    const sourceIds = ['connection-line']; // Add more if needed
    sourceIds.forEach(sourceId => {
      if (this.map.getSource(sourceId)) {
        this.map.removeSource(sourceId);
      }
    });
  }  
  
  public resetConnection(): void {
    this.firstClickedPoint = null;
    this.secondClickedPoint = null;
    if (this.map.getLayer('connection-line')) {
      this.map.removeLayer('connection-line');
      this.map.removeSource('connection-line');
    }
    if (this.map.getLayer('connection-label')) {
      this.map.removeLayer('connection-label');
    }
  }
  
  private attributeTranslations: { [key: string]: string } = {
    'WHEELCHAIR_TOILET': 'Rollstuhlgerechtes WC',
    'INFO': 'Information',
    'PRM_PLACES_AVAILABLE': 'PRM Plätze verfügbar',
    'INDUCTION_LOOP': 'Induktionsschleife',
    'OPEN_HOURS': 'Öffnungszeiten',
    'WHEELCHAIR_ACCESS': 'Rollstuhlzugang',
    'DESCRIPTION': 'Beschreibung'
  };
  }
  
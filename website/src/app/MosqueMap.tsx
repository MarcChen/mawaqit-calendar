'use client';

import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { useState } from 'react';
import CalendarSubscription from '../components/CalendarSubscription';

const parisPosition: [number, number] = [48.8566, 2.3522];

const markerIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

export default function MosqueMap({ mosqueData }) {
  return (
    <div style={{ width: '100%', height: '400px', marginTop: '1rem' }}>
      <MapContainer center={parisPosition} zoom={11} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {mosqueData.map(([key, mosque]) =>
          mosque.latitude && mosque.longitude ? (
            <Marker
              key={key}
              position={[mosque.latitude, mosque.longitude]}
              icon={markerIcon}
            >
              <Popup>
                <div style={{ textAlign: 'center', minWidth: 180 }}>
                  <strong>{mosque.name}</strong><br />
                  {mosque.url && (
                    <a href={mosque.url} target="_blank" rel="noopener noreferrer">Voir sur Mawaqit</a>
                  )}
                  <br />
                  <div style={{ display: 'flex', justifyContent: 'center', marginTop: 8 }}>
                    <CalendarSubscription
                      calendarUrl={mosque.calendarUrl}
                      mosqueName={mosque.name}
                      dropdownAlign="center"
                    />
                  </div>
                </div>
              </Popup>
            </Marker>
          ) : null
        )}
      </MapContainer>
    </div>
  );
}

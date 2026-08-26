import React, { useState, useEffect, useRef } from 'react';
import { Marker, Popup, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import {
  CloudRain,
  Mountain,
  Droplets,
  Layers,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  MapPin,
  Compass,
  Loader2,
  Sparkles,
  ExternalLink,
  ChevronRight,
} from 'lucide-react';
import { conditionAPI } from '../api';

// Regional fallback hubs for instantaneous offline / resilient reverse geocoding
const NER_HUBS = [
  { name: 'Silchar', district: 'Cachar', state: 'Assam', lat: 24.8333, lon: 92.7789 },
  { name: 'Shillong', district: 'East Khasi Hills', state: 'Meghalaya', lat: 25.5788, lon: 91.8933 },
  { name: 'Guwahati', district: 'Kamrup Metropolitan', state: 'Assam', lat: 26.1445, lon: 91.7362 },
  { name: 'Haflong', district: 'Dima Hasao', state: 'Assam', lat: 25.1833, lon: 93.0167 },
  { name: 'Majuli', district: 'Majuli', state: 'Assam', lat: 26.9500, lon: 94.2167 },
  { name: 'Aizawl', district: 'Aizawl', state: 'Mizoram', lat: 23.7271, lon: 92.7176 },
  { name: 'Imphal', district: 'Imphal West', state: 'Manipur', lat: 24.8170, lon: 93.9368 },
  { name: 'Kohima', district: 'Kohima', state: 'Nagaland', lat: 25.6751, lon: 94.1086 },
  { name: 'Agartala', district: 'West Tripura', state: 'Tripura', lat: 23.8315, lon: 91.2868 },
  { name: 'Itanagar', district: 'Papum Pare', state: 'Arunachal Pradesh', lat: 27.0844, lon: 93.6053 },
  { name: 'Gangtok', district: 'East Sikkim', state: 'Sikkim', lat: 27.3389, lon: 88.6065 },
];

function getNearestHub(lat, lon) {
  let nearest = null;
  let minDist = Infinity;
  for (const hub of NER_HUBS) {
    const dLat = hub.lat - lat;
    const dLon = hub.lon - lon;
    const dist = Math.sqrt(dLat * dLat + dLon * dLon);
    if (dist < minDist) {
      minDist = dist;
      nearest = hub;
    }
  }
  const approxKm = Math.round(minDist * 111);
  return { ...nearest, approxKm };
}

// Custom animated locator pin icon
const inspectorIcon = new L.DivIcon({
  className: 'custom-inspector-pin',
  html: `
    <div class="relative flex items-center justify-center">
      <div class="absolute w-8 h-8 rounded-full bg-blue-500/30 animate-ping"></div>
      <div class="w-6 h-6 rounded-full bg-blue-600 border-2 border-white shadow-lg flex items-center justify-center text-white">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>
      </div>
    </div>
  `,
  iconSize: [24, 24],
  iconAnchor: [12, 12],
  popupAnchor: [0, -14],
});

export default function MapLocationInspector({ onLocationSelected, autoFly = true, showDetailedPopup = true }) {
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [loading, setLoading] = useState(false);
  const [address, setAddress] = useState(null);
  const [hazardData, setHazardData] = useState(null);
  const [error, setError] = useState(null);

  const markerRef = useRef(null);
  const map = useMap();

  useMapEvents({
    async click(e) {
      const lat = parseFloat(e.latlng.lat.toFixed(5));
      const lon = parseFloat(e.latlng.lng.toFixed(5));

      setSelectedPoint({ lat, lon });
      setLoading(true);
      setError(null);
      setAddress(null);
      setHazardData(null);

      // 1. Smoothly fly/pan to clicked position
      if (autoFly) {
        map.flyTo([lat, lon], Math.max(map.getZoom(), 9), {
          duration: 0.6,
          easeLinearity: 0.25,
        });
      }

      // 2. Perform parallel Reverse Geocoding + Live AI Hazard Prediction
      try {
        // A. Reverse Geocoding with fallback
        const geocodePromise = (async () => {
          try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2500);
            const res = await fetch(
              `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=14&addressdetails=1`,
              { signal: controller.signal }
            );
            clearTimeout(timeoutId);
            if (res.ok) {
              const data = await res.json();
              const addr = data.address || {};
              const placeName =
                addr.village ||
                addr.town ||
                addr.city ||
                addr.suburb ||
                addr.county ||
                addr.district ||
                data.display_name?.split(',')[0] ||
                'Regional Corridor Location';
              const districtName = addr.county || addr.district || addr.state_district || '';
              const stateName = addr.state || 'North Eastern Region';
              return {
                placeName,
                districtName,
                stateName,
                fullAddress: data.display_name || `${placeName}, ${stateName}`,
              };
            }
          } catch {
            // Fallback to nearest hub
          }
          const hub = getNearestHub(lat, lon);
          return {
            placeName: hub.approxKm <= 5 ? hub.name : `${hub.approxKm} km from ${hub.name}`,
            districtName: hub.district,
            stateName: hub.state,
            fullAddress: `${hub.name} Corridor, ${hub.district}, ${hub.state}`,
          };
        })();

        // B. Query AI Hazard & Disruption Engine
        const hazardPromise = conditionAPI.predictRisk({
          lat,
          lon,
          use_realtime: true,
        });

        const [addrResult, hazardResult] = await Promise.all([geocodePromise, hazardPromise]);

        setAddress(addrResult);
        setHazardData(hazardResult);

        // Notify parent handler if requested
        if (onLocationSelected) {
          onLocationSelected({
            lat,
            lon,
            address: addrResult,
            hazard: hazardResult,
          });
        }
      } catch (err) {
        console.error('Failed to fetch location hazard details', err);
        setError('Could not evaluate real-time climate data for this point.');
      } finally {
        setLoading(false);
      }
    },
  });

  // Automatically open popup whenever selectedPoint updates
  useEffect(() => {
    if (selectedPoint && markerRef.current) {
      markerRef.current.openPopup();
    }
  }, [selectedPoint, loading, hazardData]);

  if (!selectedPoint) return null;

  const riskScore = hazardData?.risk_score ?? 0;
  const isCritical = hazardData?.is_critical || riskScore >= 0.7;
  const isModerate = riskScore >= 0.35 && riskScore < 0.7;
  const isLow = riskScore < 0.35;

  let riskBadgeColor = 'bg-emerald-50 text-emerald-800 border-emerald-200';
  let riskBadgeText = 'LOW HAZARD • CLEAR';
  let riskPercent = Math.round(riskScore * 100);

  if (isCritical) {
    riskBadgeColor = 'bg-red-50 text-red-800 border-red-300 font-black animate-pulse';
    riskBadgeText = 'CRITICAL RISK • LANDSLIDE/FLOOD PRONE';
  } else if (isModerate) {
    riskBadgeColor = 'bg-amber-50 text-amber-900 border-amber-300 font-bold';
    riskBadgeText = 'MODERATE RISK • CAUTION ADVISED';
  }

  const features = hazardData?.features || {};

  return (
    <Marker ref={markerRef} position={[selectedPoint.lat, selectedPoint.lon]} icon={inspectorIcon}>
      {showDetailedPopup && (
        <Popup className="setu-custom-map-popup" minWidth={310} maxWidth={340}>
          <div className="p-1 text-slate-800 font-sans">
            {/* Header with Coordinates & Location Title */}
            <div className="border-b border-slate-200/80 pb-2 mb-2">
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="text-[10px] font-mono font-bold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                  {selectedPoint.lat.toFixed(4)}°N, {selectedPoint.lon.toFixed(4)}°E
                </span>
                <span className="text-[9px] font-black uppercase text-blue-700 bg-blue-50 border border-blue-200 px-1.5 py-0.5 rounded flex items-center gap-0.5">
                  <Sparkles className="w-2.5 h-2.5" /> AI Live Sync
                </span>
              </div>
              <h4 className="text-sm font-black text-slate-900 leading-tight">
                {address?.placeName || 'Selected Corridor Location'}
              </h4>
              <p className="text-[11px] text-slate-500 font-medium leading-snug mt-0.5">
                {address?.districtName ? `${address.districtName}, ${address.stateName}` : address?.fullAddress || 'North Eastern Region'}
              </p>
            </div>

            {/* Loading Spinner */}
            {loading && (
              <div className="py-6 flex flex-col items-center justify-center space-y-2 text-center">
                <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
                <p className="text-xs font-bold text-slate-700 tracking-wide">
                  Querying Open-Meteo & NASA SRTM DEM...
                </p>
                <p className="text-[10px] text-slate-400 italic">Running Scikit-Learn Disruption Inference</p>
              </div>
            )}

            {/* Error Message */}
            {!loading && error && (
              <div className="bg-red-50 text-red-700 p-2.5 rounded border border-red-200 text-xs font-semibold my-2">
                {error}
              </div>
            )}

            {/* Real-time Environmental Hazard Data */}
            {!loading && hazardData && (
              <div className="space-y-2.5">
                {/* Threat Banner */}
                <div className={`p-2 rounded-lg border text-xs flex items-center justify-between ${riskBadgeColor}`}>
                  <div className="flex items-center gap-1.5">
                    {isCritical ? (
                      <ShieldAlert className="w-4 h-4 text-red-600 shrink-0" />
                    ) : isModerate ? (
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    ) : (
                      <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                    )}
                    <span className="text-[11px] font-black uppercase tracking-tight">{riskBadgeText}</span>
                  </div>
                  <span className="text-xs font-black tracking-tight">{riskPercent}%</span>
                </div>

                {/* 4-Tile Environmental Metrics Grid */}
                <div className="grid grid-cols-2 gap-1.5">
                  <div className="bg-slate-50 p-2 rounded-md border border-slate-200/70">
                    <div className="flex items-center gap-1 text-[10px] font-bold text-slate-500 uppercase">
                      <CloudRain className="w-3 h-3 text-blue-600" />
                      <span>24h Rainfall</span>
                    </div>
                    <div className="text-sm font-black text-slate-900 mt-0.5">
                      {features.rainfall_mm !== undefined ? `${features.rainfall_mm} mm` : '--'}
                    </div>
                  </div>

                  <div className="bg-slate-50 p-2 rounded-md border border-slate-200/70">
                    <div className="flex items-center gap-1 text-[10px] font-bold text-slate-500 uppercase">
                      <Mountain className="w-3 h-3 text-amber-600" />
                      <span>Slope Gradient</span>
                    </div>
                    <div className="text-sm font-black text-slate-900 mt-0.5">
                      {features.slope_degrees !== undefined ? `${features.slope_degrees}°` : '--'}
                    </div>
                  </div>

                  <div className="bg-slate-50 p-2 rounded-md border border-slate-200/70">
                    <div className="flex items-center gap-1 text-[10px] font-bold text-slate-500 uppercase">
                      <Compass className="w-3 h-3 text-indigo-600" />
                      <span>Elevation</span>
                    </div>
                    <div className="text-sm font-black text-slate-900 mt-0.5">
                      {features.elevation_m !== undefined ? `${Math.round(features.elevation_m)} m` : '--'}
                    </div>
                  </div>

                  <div className="bg-slate-50 p-2 rounded-md border border-slate-200/70">
                    <div className="flex items-center gap-1 text-[10px] font-bold text-slate-500 uppercase">
                      <Droplets className="w-3 h-3 text-cyan-600" />
                      <span>Soil Moisture</span>
                    </div>
                    <div className="text-sm font-black text-slate-900 mt-0.5">
                      {features.soil_saturation !== undefined
                        ? `${Math.round(features.soil_saturation * 100)}%`
                        : '--'}
                    </div>
                  </div>
                </div>

                {/* AI Explanation / Situational Insight */}
                {hazardData.explanation && (
                  <div className="bg-blue-50/70 border border-blue-100 rounded-md p-2 text-[11px] text-slate-700 leading-relaxed font-medium">
                    <div className="font-bold text-blue-900 text-[10px] uppercase mb-0.5 flex items-center gap-1">
                      <span>🤖 AI Analysis</span>
                    </div>
                    {hazardData.explanation}
                  </div>
                )}
              </div>
            )}
          </div>
        </Popup>
      )}
    </Marker>
  );
}

import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { vehicleAPI, allocationAPI, conditionAPI } from '../api';
import { IncidentImpactZoneLayer, IncidentSeverityLegend } from '../components/IncidentImpactZoneLayer';
import RealtimeTelemetryBanner from '../components/RealtimeTelemetryBanner';
import { RiskSegmentedRoute } from '../components/RiskCorridorMapLayer';
import { AlertCircle, CheckCircle, Truck, Play, RefreshCw, MapPin, Eye } from 'lucide-react';
// Custom dynamic moving cargo marker icon
const liveCargoMarkerIcon = new L.DivIcon({
  className: 'live-cargo-gps-pin',
  html: `
    <div class="relative flex items-center justify-center">
      <div class="absolute w-9 h-9 rounded-full bg-emerald-500/40 animate-ping"></div>
      <div class="w-8 h-8 rounded-full bg-slate-900 border-2 border-emerald-400 shadow-xl flex items-center justify-center text-white text-sm">
        🚚
      </div>
      <div class="absolute -bottom-5 bg-slate-900/90 text-white text-[9px] font-black px-1.5 py-0.2 rounded border border-emerald-400/40 whitespace-nowrap shadow-md">
        LIVE CARGO
      </div>
    </div>
  `,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
  popupAnchor: [0, -18],
});

function getSimulatedPosition(coordinates, progressPercent) {
  if (!coordinates || coordinates.length === 0) return null;
  if (coordinates.length === 1 || progressPercent <= 0) {
    return { lat: coordinates[0][1], lon: coordinates[0][0], pointIndex: 0 };
  }
  if (progressPercent >= 100) {
    const last = coordinates[coordinates.length - 1];
    return { lat: last[1], lon: last[0], pointIndex: coordinates.length - 1 };
  }
  const totalSegments = coordinates.length - 1;
  const rawIdx = (progressPercent / 100) * totalSegments;
  const segIdx = Math.min(Math.floor(rawIdx), totalSegments - 1);
  const segFraction = rawIdx - segIdx;

  const p1 = coordinates[segIdx];
  const p2 = coordinates[segIdx + 1];

  const lon = p1[0] + (p2[0] - p1[0]) * segFraction;
  const lat = p1[1] + (p2[1] - p1[1]) * segFraction;
  return { lat, lon, pointIndex: segIdx };
}

export default function TransportPortal() {
  const { user } = useAuth();
  const [vehicles, setVehicles] = useState([]);
  const [allocations, setAllocations] = useState([]);
  const [conditions, setConditions] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [selectedAllocation, setSelectedAllocation] = useState(null);
  const [loading, setLoading] = useState(false);

  // New vehicle form
  const [newVehicle, setNewVehicle] = useState({
    registration_number: '',
    vehicle_type: '5-Ton Truck',
  });
  const [vehicleMsg, setVehicleMsg] = useState({ text: '', type: '' });
  const [registering, setRegistering] = useState(false);

  // Tracking / Simulation states
  const [pingMsg, setPingMsg] = useState({ text: '', type: '' });
  const [isSimulating, setIsSimulating] = useState(false);
  const [simIntervalId, setSimIntervalId] = useState(null);
  const [simProgressPercent, setSimProgressPercent] = useState(50); // Default to 50% Midway for instant inspection

  useEffect(() => {
    fetchLogisticsData();
    return () => {
      if (simIntervalId) clearInterval(simIntervalId);
    };
  }, []);

  const fetchLogisticsData = async () => {
    setLoading(true);
    try {
      const params = {};
      if (user?.role === 'transport_operator') {
        params.operator = user.id;
      }
      const vData = await vehicleAPI.list(params);
      setVehicles(vData.results || vData || []);

      const aData = await allocationAPI.list();
      // Filter allocations for this operator's vehicles or show all if admin/other
      const vIds = (vData.results || vData || []).map((v) => v.id);
      const opAllocs = user?.role === 'transport_operator'
        ? (aData.results || aData || []).filter((a) => vIds.includes(a.vehicle))
        : (aData.results || aData || []);
      setAllocations(opAllocs);

      const cData = await conditionAPI.list();
      setConditions(cData.results || cData || []);
    } catch (err) {
      console.error('Error fetching logistics data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterVehicle = async (e) => {
    e.preventDefault();
    if (!newVehicle.registration_number) {
      setVehicleMsg({ text: 'Registration number required.', type: 'error' });
      return;
    }
    setRegistering(true);
    setVehicleMsg({ text: '', type: '' });
    try {
      const payload = {
        ...newVehicle,
        operator: user?.id,
        latitude: 24.83,
        longitude: 92.78,
        status: 'idle',
      };
      const v = await vehicleAPI.create(payload);
      setVehicles([...vehicles, v]);
      setVehicleMsg({ text: `Vehicle ${v.registration_number} registered.`, type: 'success' });
      setNewVehicle({ registration_number: '', vehicle_type: '5-Ton Truck' });
    } catch (err) {
      setVehicleMsg({ text: 'Registration failed. Registration number must be unique.', type: 'error' });
    } finally {
      setRegistering(false);
    }
  };

  const updateAllocationStatus = async (id, status) => {
    try {
      const updated = await allocationAPI.update(id, { delivery_status: status });
      // Update allocations list
      setAllocations(allocations.map((a) => (a.id === id ? updated : a)));
      setSelectedAllocation(updated);
      
      // Update vehicle status locally if status changed
      if (status === 'delivered') {
        const vId = updated.vehicle;
        await vehicleAPI.ping(vId, { latitude: 24.83, longitude: 92.78, status: 'idle' });
        fetchLogisticsData();
      }
    } catch (err) {
      console.error('Failed to update allocation milestone', err);
    }
  };

  const handleSetSimulationProgress = async (allocation, percent) => {
    setSimProgressPercent(percent);
    const coords = allocation?.route_geojson?.geometry?.coordinates;
    if (!coords || coords.length === 0) return;

    const pos = getSimulatedPosition(coords, percent);
    if (!pos) return;

    const statusLabel =
      percent === 0
        ? 'Origin Depot'
        : percent >= 100
        ? 'Destination Sector'
        : percent === 50
        ? 'Midway Transit'
        : `${percent}% in transit`;

    try {
      if (allocation.vehicle) {
        await vehicleAPI.ping(allocation.vehicle, {
          latitude: pos.lat,
          longitude: pos.lon,
          status: percent >= 100 ? 'idle' : 'en_route',
        });
      }
      setPingMsg({
        text: `Live GPS Ping (${percent}%): Lat ${pos.lat.toFixed(4)}°N, Lon ${pos.lon.toFixed(4)}°E — ${statusLabel}`,
        type: 'info',
      });
    } catch {
      setPingMsg({
        text: `Simulated GPS (${percent}%): Lat ${pos.lat.toFixed(4)}°N, Lon ${pos.lon.toFixed(4)}°E — ${statusLabel}`,
        type: 'info',
      });
    }
  };

  const handleTogglePlaySimulation = (allocation) => {
    if (isSimulating) {
      if (simIntervalId) clearInterval(simIntervalId);
      setIsSimulating(false);
      setSimIntervalId(null);
      setPingMsg({ text: 'GPS simulation paused.', type: 'info' });
      return;
    }

    if (!allocation?.route_geojson) return;
    const coords = allocation.route_geojson.geometry?.coordinates;
    if (!coords || coords.length === 0) return;

    setIsSimulating(true);
    setPingMsg({ text: 'Live GPS convoy simulation active...', type: 'success' });

    let currentPct = simProgressPercent >= 100 ? 0 : simProgressPercent;

    const intervalId = setInterval(async () => {
      currentPct += 2;
      if (currentPct > 100) {
        currentPct = 100;
        clearInterval(intervalId);
        setIsSimulating(false);
        setSimIntervalId(null);
        setSimProgressPercent(100);
        await updateAllocationStatus(allocation.id, 'delivered');
        setPingMsg({ text: 'Vehicle reached destination sector. Status: Delivered.', type: 'success' });
        return;
      }

      setSimProgressPercent(currentPct);
      const pos = getSimulatedPosition(coords, currentPct);
      if (pos && allocation.vehicle) {
        try {
          await vehicleAPI.ping(allocation.vehicle, {
            latitude: pos.lat,
            longitude: pos.lon,
            status: 'en_route',
          });
        } catch {}
      }
    }, 650);

    setSimIntervalId(intervalId);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="border-b border-slate-200 pb-4 mb-6">
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 flex items-center space-x-2">
          <Truck className="h-6 w-6 text-primary-600 animate-bounce shrink-0" />
          <span>Transport Operator Control Center</span>
        </h1>
        <p className="text-sm text-slate-500 font-medium">
          Register logistics vehicles, track dispatch allocations, and simulate real-time GPS telemetry routing.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* left column: fleet list & vehicle register */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2 mb-4 border-b border-slate-100 pb-2">
              <Truck className="h-5 w-5 text-primary-600" />
              <span>Register Vehicle</span>
            </h2>

            {vehicleMsg.text && (
              <div
                className={`p-3 rounded text-xs mb-4 flex items-center space-x-2 font-medium border ${
                  vehicleMsg.type === 'success'
                    ? 'bg-green-50 border-green-200 text-green-700'
                    : 'bg-red-50 border-red-200 text-red-700'
                }`}
              >
                {vehicleMsg.type === 'success' ? (
                  <CheckCircle className="h-4 w-4 shrink-0" />
                ) : (
                  <AlertCircle className="h-4 w-4 shrink-0" />
                )}
                <span>{vehicleMsg.text}</span>
              </div>
            )}

            <form onSubmit={handleRegisterVehicle} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1 uppercase tracking-wider">
                  Registration Number *
                </label>
                <input
                  name="registration_number"
                  type="text"
                  required
                  placeholder="e.g. AS-01-AB-1234"
                  value={newVehicle.registration_number}
                  onChange={(e) => setNewVehicle({ ...newVehicle, registration_number: e.target.value })}
                  className="w-full text-sm border border-slate-200 rounded p-2"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1 uppercase tracking-wider">
                  Vehicle Type
                </label>
                <select
                  name="vehicle_type"
                  value={newVehicle.vehicle_type}
                  onChange={(e) => setNewVehicle({ ...newVehicle, vehicle_type: e.target.value })}
                  className="w-full text-sm border border-slate-200 rounded p-2 bg-white"
                >
                  <option value="5-Ton Heavy Truck">5-Ton Heavy Truck</option>
                  <option value="4x4 Rescue Pickup">4x4 Rescue Pickup</option>
                  <option value="SDRF Inflatable Motorboat">SDRF Inflatable Motorboat</option>
                  <option value="Emergency Ambulance">Emergency Ambulance</option>
                  <option value="Standard Cargo Van">Standard Cargo Van</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={registering}
                className="w-full py-3 bg-primary hover:bg-primary/90 text-on-primary font-bold uppercase text-xs rounded-md shadow-md transition-all cursor-pointer disabled:opacity-50 tracking-wider mt-2"
              >
                {registering ? 'Registering...' : 'Add Vehicle to Fleet'}
              </button>
            </form>
          </div>

          {/* Fleet status card */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2 mb-4 border-b border-slate-100 pb-2">
              <Truck className="h-5 w-5 text-primary-600" />
              <span>Fleet Registry ({vehicles.length})</span>
            </h2>
            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {vehicles.map((v) => (
                <div
                  key={v.id}
                  onClick={() => setSelectedVehicle(v)}
                  className={`p-3 rounded border text-xs font-semibold cursor-pointer transition-colors ${
                    selectedVehicle?.id === v.id
                      ? 'border-primary-500 bg-primary-50 text-primary-800'
                      : 'border-slate-100 hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-extrabold">{v.registration_number}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[9px] font-black uppercase ${
                        v.status === 'idle'
                          ? 'bg-green-100 text-green-800'
                          : v.status === 'en_route'
                          ? 'bg-blue-100 text-blue-800 animate-pulse'
                          : 'bg-slate-100 text-slate-800'
                      }`}
                    >
                      {v.status}
                    </span>
                  </div>
                  <div className="text-slate-500 mt-1">{v.vehicle_type}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* middle/right column: active allocations, map, GPS simulator */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Allocations */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2 mb-4 border-b border-slate-100 pb-2">
              <Truck className="h-5 w-5 text-primary-600" />
              <span>Active Delivery Allocations ({allocations.length})</span>
            </h2>

            {allocations.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No delivery allocations currently assigned to your fleet.</p>
            ) : (
              <div className="space-y-4">
                {allocations.map((a) => (
                  <div
                    key={a.id}
                    className={`p-4 rounded-md border text-xs font-semibold shadow-sm transition-all cursor-pointer ${
                      selectedAllocation?.id === a.id
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-slate-100 hover:bg-slate-50 bg-white'
                    }`}
                    onClick={() => setSelectedAllocation(a)}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-3 border-b border-slate-100 pb-2">
                      <div className="flex items-center space-x-2">
                        <span className="bg-slate-200 text-slate-800 px-2 py-0.5 rounded text-[10px] font-extrabold uppercase">
                          ALLOCATION #{a.id}
                        </span>
                        <span className="text-[10px] text-slate-400">Assigned {new Date(a.assigned_at).toLocaleDateString()}</span>
                      </div>
                      <span
                        className={`mt-2 sm:mt-0 px-2.5 py-0.5 rounded text-[10px] font-black uppercase border ${
                          a.delivery_status === 'delivered'
                            ? 'bg-green-100 text-green-800 border-green-200'
                            : a.delivery_status === 'delayed'
                            ? 'bg-red-100 text-red-800 border-red-200 animate-pulse'
                            : 'bg-blue-100 text-blue-800 border-blue-200'
                        }`}
                      >
                        {a.delivery_status}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-slate-600 mb-3">
                      <div>
                        <strong>Cargo Type:</strong> <span className="uppercase text-slate-900 font-bold">{a.need_type.replace('_', ' ')}</span>
                      </div>
                      <div>
                        <strong>Load Volume:</strong> {a.need_quantity} {a.need_unit}
                      </div>
                      <div>
                        <strong>Assigned Vehicle:</strong> {a.vehicle_registration || 'None'}
                      </div>
                      <div>
                        <strong>Estimated Delay:</strong> <span className={a.estimated_delay_minutes > 0 ? 'text-red-500 font-bold' : ''}>{a.estimated_delay_minutes} mins</span>
                      </div>
                    </div>

                    {/* Milestones Action Controls */}
                    {a.delivery_status !== 'delivered' && (
                      <div className="flex flex-wrap gap-2 border-t border-slate-100 pt-3">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            updateAllocationStatus(a.id, 'en_route');
                          }}
                          className="px-3 py-1 border border-primary-300 text-primary-700 bg-white rounded text-[10px] font-bold hover:bg-primary-50 transition-colors"
                        >
                          En Route Milestone
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            updateAllocationStatus(a.id, 'delivered');
                          }}
                          className="px-3 py-1 border border-green-300 text-green-700 bg-white rounded text-[10px] font-bold hover:bg-green-50 transition-colors"
                        >
                          Delivered Milestone
                        </button>
                        {a.route_geojson && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleStartSimulation(a);
                            }}
                            disabled={isSimulating}
                            className="px-3 py-1 bg-primary-600 text-white rounded text-[10px] font-bold hover:bg-primary-700 transition-colors flex items-center space-x-1 disabled:opacity-50"
                          >
                            <Play className="h-3 w-3" />
                            <span>Simulate Transit GPS Pings</span>
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* GeoJSON Map View & GPS Telemetry Simulator logs */}
          {selectedAllocation && (
            <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <h3 className="text-sm font-bold text-slate-800 flex items-center space-x-2">
                  <MapPin className="h-4.5 w-4.5 text-primary-600" />
                  <span>Transit Geonavigator Map — Allocation #{selectedAllocation.id}</span>
                </h3>
                <span className="text-[10px] text-slate-400 font-extrabold uppercase bg-slate-100 px-2 py-0.5 rounded">
                  {selectedAllocation.delivery_status}
                </span>
              </div>

              {pingMsg.text && (
                <div
                  className={`p-3 rounded text-xs flex items-center space-x-2 font-semibold border ${
                    pingMsg.type === 'success'
                      ? 'bg-green-50 border-green-200 text-green-700'
                      : pingMsg.type === 'info'
                      ? 'bg-blue-50 border-blue-200 text-blue-700 animate-pulse'
                      : 'bg-red-50 border-red-200 text-red-700'
                  }`}
                >
                  <RefreshCw className={`h-4 w-4 shrink-0 ${pingMsg.type === 'info' ? 'animate-spin' : ''}`} />
                  <span>{pingMsg.text}</span>
                </div>
              )}

              {selectedAllocation.route_geojson ? (
                <div className="space-y-3">
                  {/* Interactive Vehicle Simulation Control Panel */}
                  <div className="bg-slate-900 text-white p-4 rounded-xl shadow-sm space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-2.5">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-md bg-emerald-500 text-slate-950 font-black flex items-center justify-center text-xs">
                          GPS
                        </div>
                        <div>
                          <div className="text-xs font-black uppercase tracking-wider text-slate-100 flex items-center gap-2">
                            <span>Cargo Vehicle Simulation & Live Telemetry</span>
                            <span className="text-[9px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-500/30">
                              {simProgressPercent}% Transit Progress
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Play / Pause Toggle Button */}
                      <button
                        type="button"
                        onClick={() => handleTogglePlaySimulation(selectedAllocation)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-extrabold flex items-center gap-1.5 transition-all shadow-sm ${
                          isSimulating
                            ? 'bg-amber-500 hover:bg-amber-600 text-slate-950'
                            : 'bg-emerald-500 hover:bg-emerald-600 text-slate-950'
                        }`}
                      >
                        {isSimulating ? (
                          <>
                            <span className="w-2 h-2 rounded-full bg-slate-950 animate-ping" />
                            <span>Pause Simulation</span>
                          </>
                        ) : (
                          <>
                            <Play className="w-3.5 h-3.5 fill-current" />
                            <span>Play GPS Simulation</span>
                          </>
                        )}
                      </button>
                    </div>

                    {/* Progress Slider */}
                    <div>
                      <div className="flex justify-between text-[11px] font-bold text-slate-400 mb-1">
                        <span>Depot (0%)</span>
                        <span className="text-emerald-400 font-extrabold">Current: {simProgressPercent}%</span>
                        <span>Destination (100%)</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        step="1"
                        value={simProgressPercent}
                        onChange={(e) =>
                          handleSetSimulationProgress(selectedAllocation, parseInt(e.target.value, 10))
                        }
                        className="w-full accent-emerald-500 cursor-pointer h-2 bg-slate-800 rounded-lg"
                      />
                    </div>

                    {/* Quick Preset Jump Buttons (Origin, Midway 50%, Destination) */}
                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      <span className="text-[10px] uppercase font-bold text-slate-400">Quick Jump:</span>
                      <button
                        type="button"
                        onClick={() => handleSetSimulationProgress(selectedAllocation, 0)}
                        className={`px-2.5 py-1 rounded text-[10px] font-bold transition-colors ${
                          simProgressPercent === 0
                            ? 'bg-emerald-500 text-slate-950'
                            : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
                        }`}
                      >
                        Origin Depot (0%)
                      </button>
                      <button
                        type="button"
                        onClick={() => handleSetSimulationProgress(selectedAllocation, 50)}
                        className={`px-2.5 py-1 rounded text-[10px] font-black transition-colors flex items-center gap-1 ${
                          simProgressPercent === 50
                            ? 'bg-amber-400 text-slate-950 ring-2 ring-amber-300'
                            : 'bg-slate-800 hover:bg-slate-700 text-amber-300'
                        }`}
                      >
                        <span>⚡ Midway (50%)</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => handleSetSimulationProgress(selectedAllocation, 85)}
                        className={`px-2.5 py-1 rounded text-[10px] font-bold transition-colors ${
                          simProgressPercent === 85
                            ? 'bg-emerald-500 text-slate-950'
                            : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
                        }`}
                      >
                        Near Target (85%)
                      </button>
                      <button
                        type="button"
                        onClick={() => handleSetSimulationProgress(selectedAllocation, 100)}
                        className={`px-2.5 py-1 rounded text-[10px] font-bold transition-colors ${
                          simProgressPercent === 100
                            ? 'bg-emerald-500 text-slate-950'
                            : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
                        }`}
                      >
                        Delivered (100%)
                      </button>
                    </div>
                  </div>

                  {/* Map Box */}
                  <div className="w-full h-96 relative rounded-xl border border-slate-200 overflow-hidden shadow-xs">
                    <MapContainer
                      center={[
                        selectedAllocation.route_geojson.geometry.coordinates[0][1],
                        selectedAllocation.route_geojson.geometry.coordinates[0][0],
                      ]}
                      zoom={11}
                      className="w-full h-full"
                    >
                      <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      />

                      {/* Real-time Color-Coded Incident Impact Area Layer */}
                      <IncidentImpactZoneLayer conditions={conditions} />

                      {/* 3-Tier Color Coded Dispatch Route */}
                      {(() => {
                        const routePts = selectedAllocation.route_geojson.geometry.coordinates.map((c) => [c[1], c[0]]);
                        const isDelayed = selectedAllocation.delivery_status === 'delayed';
                        const delayRiskVal = selectedAllocation.match_details?.score_breakdown?.delay_risk;
                        const calculatedRisk = isDelayed
                          ? 0.86
                          : delayRiskVal !== undefined
                          ? 1.0 - parseFloat(delayRiskVal)
                          : 0.22;

                        return (
                          <RiskSegmentedRoute
                            routeCoordinates={routePts}
                            riskScore={calculatedRisk}
                            label={`Transit Dispatch #${selectedAllocation.id}`}
                            statusText={selectedAllocation.delivery_status.replace('_', ' ').toUpperCase()}
                            originName={selectedAllocation.match_details?.resource_details?.provider_username || 'Depot'}
                            destName={selectedAllocation.match_details?.need_details?.district_name || 'Relief Target'}
                          />
                        );
                      })()}
                      
                      {/* Source Stockpile Marker */}
                      <Marker
                        position={[
                          selectedAllocation.route_geojson.geometry.coordinates[0][1],
                          selectedAllocation.route_geojson.geometry.coordinates[0][0],
                        ]}
                      >
                        <Popup>
                          <div className="text-xs p-1 font-bold text-slate-800">
                            📦 Source Depot Stockpile
                          </div>
                        </Popup>
                      </Marker>

                      {/* Destination Need Marker */}
                      <Marker
                        position={[
                          selectedAllocation.route_geojson.geometry.coordinates[
                            selectedAllocation.route_geojson.geometry.coordinates.length - 1
                          ][1],
                          selectedAllocation.route_geojson.geometry.coordinates[
                            selectedAllocation.route_geojson.geometry.coordinates.length - 1
                          ][0],
                        ]}
                      >
                        <Popup>
                          <div className="text-xs p-1 font-bold text-slate-800">
                            🎯 Target Relief Need Sector
                          </div>
                        </Popup>
                      </Marker>

                      {/* Dynamic Simulated Moving Cargo GPS Marker */}
                      {(() => {
                        const coords = selectedAllocation.route_geojson?.geometry?.coordinates;
                        const simPos = getSimulatedPosition(coords, simProgressPercent);
                        if (!simPos) return null;

                        return (
                          <Marker position={[simPos.lat, simPos.lon]} icon={liveCargoMarkerIcon}>
                            <Popup>
                              <div className="text-xs p-1 text-slate-900 font-sans space-y-1">
                                <div className="font-extrabold text-emerald-700 flex items-center gap-1">
                                  <span>🚚 Convoy Vehicle #{selectedAllocation.vehicle}</span>
                                </div>
                                <div className="text-[11px] font-bold text-slate-800">
                                  Progress: {simProgressPercent}% {simProgressPercent === 50 ? '(Midway in transit)' : ''}
                                </div>
                                <div className="text-[10px] font-mono text-slate-500">
                                  GPS: {simPos.lat.toFixed(4)}°N, {simPos.lon.toFixed(4)}°E
                                </div>
                                <div className="text-[10px] text-slate-600 font-semibold bg-slate-100 p-1 rounded">
                                  Status: {simProgressPercent >= 100 ? 'Arrived at Destination' : simProgressPercent === 50 ? 'Cruising Midway Pass' : 'En Route to Target'}
                                </div>
                              </div>
                            </Popup>
                          </Marker>
                        );
                      })()}
                    </MapContainer>

                    {/* Real-time Severity Divisions Legend */}
                    <IncidentSeverityLegend
                      totalIncidents={conditions.length}
                      className="absolute bottom-3 right-3 shadow-xl"
                    />
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">No route geo-geometry calculated for this transit allocation.</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import { conditionAPI, districtAPI } from '../api';
import {
  IncidentImpactZoneLayer,
  IncidentSeverityLegend,
  getIncidentSeverity,
} from '../components/IncidentImpactZoneLayer';
import RealtimeTelemetryBanner from '../components/RealtimeTelemetryBanner';
import {
  RiskSegmentedRoute,
  getRiskDivision,
  NER_HIGHWAY_CORRIDORS,
} from '../components/RiskCorridorMapLayer';
import MapLocationInspector from '../components/MapLocationInspector';
import {
  AlertCircle,
  CheckCircle,
  MapPin,
  Cpu,
  Upload,
  Compass,
  Eye,
  ShieldAlert,
  Route,
  AlertTriangle,
  Activity,
  Navigation,
  ChevronRight,
  Layers,
  Radio,
} from 'lucide-react';
import L from 'leaflet';

// Leaflet click handler helper
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export default function FieldOfficerPortal() {
  const [activeTab, setActiveTab] = useState('report'); // 'report' or 'ai_predict'
  const [districts, setDistricts] = useState([]);
  const [conditions, setConditions] = useState([]);
  
  // Incident Report Form States
  const [reportForm, setReportForm] = useState({
    condition_type: 'road_status',
    value: 'blocked',
    latitude: 24.8333,
    longitude: 92.7789,
    district: '',
    risk_score: '0.85',
    radius_meters: 1400,
  });
  const [reportFile, setReportFile] = useState(null);
  const [reportMsg, setReportMsg] = useState({ text: '', type: '' });
  const [reportSubmitting, setReportSubmitting] = useState(false);
  const [isRefreshingTelemetry, setIsRefreshingTelemetry] = useState(false);

  // AI Predictor States
  const [predictMode, setPredictMode] = useState('route'); // 'route' (corridor range) or 'single' (point)
  const [selectedCorridorId, setSelectedCorridorId] = useState('corridor-nh6-shillong-silchar');
  const [routeWaypoints, setRouteWaypoints] = useState(NER_HIGHWAY_CORRIDORS[0]?.path || []);
  const [routeBufferKm, setRouteBufferKm] = useState(5.0);
  const [customWaypointText, setCustomWaypointText] = useState('');

  const [aiForm, setAiForm] = useState({
    latitude: 24.8333,
    longitude: 92.7789,
    rainfall: '',
    slope: '',
    elevation: '',
    soil_saturation: '',
    drainage: '',
    vegetation: '',
    use_realtime: true,
  });
  const [predictMsg, setPredictMsg] = useState({ text: '', type: '' });
  const [predictLoading, setPredictLoading] = useState(false);
  const [predictStep, setPredictStep] = useState('');
  const [predictResult, setPredictResult] = useState(null);

  const fetchConditionsAndDistricts = useCallback(async () => {
    setIsRefreshingTelemetry(true);
    try {
      const data = await districtAPI.list();
      setDistricts(data.results || data || []);

      const cData = await conditionAPI.list();
      setConditions(cData.results || cData || []);
    } catch (err) {
      console.error('Failed to load districts/conditions', err);
    } finally {
      setIsRefreshingTelemetry(false);
    }
  }, []);

  useEffect(() => {
    fetchConditionsAndDistricts();
    // Real-time polling every 25 seconds
    const interval = setInterval(fetchConditionsAndDistricts, 25000);
    return () => clearInterval(interval);
  }, [fetchConditionsAndDistricts]);

  const handleReportChange = (e) => {
    setReportForm({ ...reportForm, [e.target.name]: e.target.value });
  };

  const handleReportMapClick = (lat, lng) => {
    setReportForm((prev) => ({
      ...prev,
      latitude: parseFloat(lat.toFixed(5)),
      longitude: parseFloat(lng.toFixed(5)),
    }));
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setReportFile(e.target.files[0]);
    }
  };

  const handleSubmitReport = async (e) => {
    e.preventDefault();
    setReportSubmitting(true);
    setReportMsg({ text: '', type: '' });
    try {
      const payload = {
        ...reportForm,
        risk_score: reportForm.risk_score ? parseFloat(reportForm.risk_score) : 0.85,
        district: reportForm.district ? parseInt(reportForm.district, 10) : null,
      };

      const condition = await conditionAPI.create(payload);
      
      // If file uploaded, trigger attachment endpoint
      if (reportFile) {
        setReportMsg({ text: 'Uploading media attachment...', type: 'info' });
        await conditionAPI.uploadAttachment(condition.id, reportFile, 'photo');
      }

      // Immediately show the new colored affected zone on the live map
      const districtObj = districts.find((d) => d.id === parseInt(reportForm.district, 10));
      const enrichedCondition = {
        ...condition,
        latitude: payload.latitude,
        longitude: payload.longitude,
        risk_score: payload.risk_score,
        condition_type: payload.condition_type,
        value: payload.value,
        district_name: districtObj?.name || 'Local Sector',
        reported_at: new Date().toISOString(),
      };
      setConditions((prev) => [enrichedCondition, ...prev]);

      setReportMsg({ text: 'Ground condition reported successfully! Impact zone color-marked on live map.', type: 'success' });
      setReportForm({
        condition_type: 'road_status',
        value: 'blocked',
        latitude: 24.8333,
        longitude: 92.7789,
        district: '',
        risk_score: '0.85',
        radius_meters: 1400,
      });
      setReportFile(null);
    } catch (err) {
      setReportMsg({ text: 'Failed to log condition. Verify coordinates.', type: 'error' });
    } finally {
      setReportSubmitting(false);
    }
  };

  // AI Predictor Logic
  const handleCorridorSelect = (corridorId) => {
    setSelectedCorridorId(corridorId);
    if (corridorId === 'custom') {
      return;
    }
    const found = NER_HIGHWAY_CORRIDORS.find((c) => c.id === corridorId);
    if (found) {
      setRouteWaypoints(found.path);
      setCustomWaypointText(found.path.map((p) => `${p[0]}, ${p[1]}`).join('\n'));
    }
  };

  const handleCustomWaypointChange = (e) => {
    const txt = e.target.value;
    setCustomWaypointText(txt);
    const pts = txt
      .split('\n')
      .map((l) => {
        const parts = l.split(',');
        if (parts.length >= 2) {
          const lat = parseFloat(parts[0].trim());
          const lon = parseFloat(parts[1].trim());
          if (!isNaN(lat) && !isNaN(lon)) return [lat, lon];
        }
        return null;
      })
      .filter(Boolean);
    if (pts.length > 0) {
      setRouteWaypoints(pts);
    }
  };

  const handleAiChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setAiForm({ ...aiForm, [e.target.name]: value });
  };

  const handleAiMapClick = (lat, lng) => {
    const latVal = parseFloat(lat.toFixed(5));
    const lonVal = parseFloat(lng.toFixed(5));
    if (predictMode === 'route') {
      const newPt = [latVal, lonVal];
      const updated = [...routeWaypoints, newPt];
      setRouteWaypoints(updated);
      setSelectedCorridorId('custom');
      setCustomWaypointText(updated.map((p) => `${p[0]}, ${p[1]}`).join('\n'));
    } else {
      setAiForm((prev) => ({
        ...prev,
        latitude: latVal,
        longitude: lonVal,
      }));
      // Auto-trigger prediction when clicking the map in single point mode!
      triggerAIPrediction(null, latVal, lonVal);
    }
  };

  const triggerAIPrediction = async (e, directLat = null, directLon = null) => {
    if (e) e.preventDefault();
    setPredictLoading(true);
    setPredictResult(null);
    setPredictMsg({ text: '', type: '' });

    const latVal = directLat !== null ? directLat : aiForm.latitude;
    const lonVal = directLon !== null ? directLon : aiForm.longitude;

    const stepMessages = predictMode === 'route' ? [
      `Sampling spatial corridor range nodes (${routeWaypoints.length} waypoints)...`,
      'Querying Open-Meteo rolling precipitation & NASA SRTM DEM for all corridor nodes...',
      'Executing Gradient Boosting inference pipeline & calculating spatial delta gradients...',
      'Evaluating localized micro-anomalies (rain surges, slope breaks, subgrade saturation)...',
      'Synthesizing composite corridor threat score and contiguous hazard sub-ranges...',
    ] : [
      'Establishing connection with Open-Meteo REST endpoint...',
      'Retrieving NASA Shuttle Radar Topography Mission (SRTM) DEM point sample...',
      'Extracting cloud-filtered Sentinel-2 NDVI vegetative composites...',
      'Calculating local terrain slope spatial finite difference gradient...',
      'Synthesizing features and executing Scikit-Learn Gradient Boosting Risk model...',
    ];

    let currentStep = 0;
    setPredictStep(stepMessages[0]);
    
    // Simulate pipeline stage indicators in the UI
    const interval = setInterval(() => {
      currentStep++;
      if (currentStep < stepMessages.length) {
        setPredictStep(stepMessages[currentStep]);
      }
    }, 600);

    try {
      if (predictMode === 'route') {
        const payload = {
          waypoints: routeWaypoints,
          buffer_km: routeBufferKm,
          use_realtime: aiForm.use_realtime,
        };
        const res = await conditionAPI.predictRouteRisk(payload);
        clearInterval(interval);
        setPredictResult(res);
      } else {
        const params = {
          lat: latVal,
          lon: lonVal,
          use_realtime: aiForm.use_realtime,
        };

        if (aiForm.rainfall) params.rainfall = parseFloat(aiForm.rainfall);
        if (aiForm.slope) params.slope = parseFloat(aiForm.slope);
        if (aiForm.elevation) params.elevation = parseFloat(aiForm.elevation);
        if (aiForm.soil_saturation) params.soil_saturation = parseFloat(aiForm.soil_saturation);
        if (aiForm.drainage) params.drainage = parseFloat(aiForm.drainage);
        if (aiForm.vegetation) params.vegetation = parseFloat(aiForm.vegetation);

        const res = await conditionAPI.predictRisk(params);
        clearInterval(interval);
        setPredictResult(res);
      }
    } catch (err) {
      clearInterval(interval);
      setPredictMsg({ text: 'AI inference pipeline failed. Check internet access or parameters.', type: 'error' });
    } finally {
      setPredictLoading(false);
      setPredictStep('');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="border-b border-slate-200 pb-4 mb-6 flex flex-col md:flex-row md:items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 flex items-center space-x-2">
            <Compass className="h-6 w-6 text-primary-600" />
            <span>Field Officer Portal</span>
          </h1>
          <p className="text-sm text-slate-500 font-medium">
            Log active road blocks and trigger real-time geo-climatic risk predictions.
          </p>
        </div>

        <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200 mt-4 md:mt-0 font-semibold self-start">
          <button
            onClick={() => setActiveTab('report')}
            className={`px-4 py-1.5 rounded-md text-xs transition-colors ${
              activeTab === 'report' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            Report Incident
          </button>
          <button
            onClick={() => setActiveTab('ai_predict')}
            className={`px-4 py-1.5 rounded-md text-xs transition-colors flex items-center space-x-1.5 ${
              activeTab === 'ai_predict' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            <Cpu className="h-3.5 w-3.5" />
            <span>AI Risk Analyzer</span>
          </button>
        </div>
      </div>

      {/* Real-Time Live Telemetry Bar */}
      <RealtimeTelemetryBanner
        conditions={conditions}
        districtName={districts[0]?.name || 'Cachar / Barak Valley'}
        onRefresh={fetchConditionsAndDistricts}
        isRefreshing={isRefreshingTelemetry}
      />

      {activeTab === 'report' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Form */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
              <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2 mb-4 border-b border-slate-100 pb-2">
                <Upload className="h-5 w-5 text-primary-600" />
                <span>Log Obstruction / Hazard</span>
              </h2>

              {reportMsg.text && (
                <div
                  className={`p-3 rounded text-xs mb-4 flex items-center space-x-2 font-medium border ${
                    reportMsg.type === 'success'
                      ? 'bg-green-50 border-green-200 text-green-700'
                      : reportMsg.type === 'info'
                      ? 'bg-blue-50 border-blue-200 text-blue-700'
                      : 'bg-red-50 border-red-200 text-red-700'
                  }`}
                >
                  {reportMsg.type === 'success' ? (
                    <CheckCircle className="h-4 w-4 shrink-0" />
                  ) : reportMsg.type === 'info' ? (
                    <Compass className="h-4 w-4 shrink-0 animate-spin" />
                  ) : (
                    <AlertCircle className="h-4 w-4 shrink-0" />
                  )}
                  <span>{reportMsg.text}</span>
                </div>
              )}

              <form onSubmit={handleSubmitReport} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1 uppercase tracking-wider">
                    Condition Type
                  </label>
                  <select
                    name="condition_type"
                    value={reportForm.condition_type}
                    onChange={handleReportChange}
                    className="w-full text-sm border border-slate-200 rounded p-2 bg-white"
                  >
                    <option value="road_status">Road Status / Obstruction</option>
                    <option value="rainfall">Rainfall Ingress (mm)</option>
                    <option value="landslide_risk">Landslide Risk Level</option>
                    <option value="traffic">Traffic Corridor Congestion</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1 uppercase tracking-wider">
                    Status / Value
                  </label>
                  <select
                    name="value"
                    value={reportForm.value}
                    onChange={handleReportChange}
                    className="w-full text-sm border border-slate-200 rounded p-2 bg-white"
                  >
                    <option value="blocked">Blocked / Impassable</option>
                    <option value="flooded">Flooded / High Inundation</option>
                    <option value="landslide">Active Landslide Cut-off</option>
                    <option value="clear">Clear / Passable</option>
                    <option value="closed">Closed by SDRF/District Admin</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1 uppercase tracking-wider">
                      District
                    </label>
                    <select
                      name="district"
                      value={reportForm.district}
                      onChange={handleReportChange}
                      className="w-full text-sm border border-slate-200 rounded p-2 bg-white"
                    >
                      <option value="">Select District</option>
                      {districts.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1 uppercase tracking-wider">
                      Assigned Risk Score (Optional)
                    </label>
                    <input
                      name="risk_score"
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      placeholder="0.0 - 1.0"
                      value={reportForm.risk_score}
                      onChange={handleReportChange}
                      className="w-full text-sm border border-slate-200 rounded p-2"
                    />
                  </div>
                </div>

                {/* Impact Area Radius Buffer Selector */}
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1 uppercase tracking-wider">
                    Affected Impact Area Radius
                  </label>
                  <div className="grid grid-cols-4 gap-1.5 text-xs">
                    {[
                      { label: '500m', value: 500, desc: 'Spot Hazard' },
                      { label: '1.0 km', value: 1000, desc: 'Road Stretch' },
                      { label: '1.5 km', value: 1400, desc: 'Pass / Valley' },
                      { label: '2.5 km', value: 2500, desc: 'Wide Flood' },
                    ].map((rad) => (
                      <button
                        key={rad.value}
                        type="button"
                        onClick={() => setReportForm({ ...reportForm, radius_meters: rad.value })}
                        className={`p-1.5 rounded-lg border text-center font-bold transition-all cursor-pointer ${
                          reportForm.radius_meters === rad.value
                            ? 'bg-primary text-white border-primary shadow-xs'
                            : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                        }`}
                      >
                        <div>{rad.label}</div>
                        <div className="text-[9px] opacity-80 font-normal">{rad.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1 uppercase tracking-wider">
                    Coordinates (Click Map to autofill)
                  </label>
                  <div className="flex space-x-2">
                    <input
                      name="latitude"
                      type="number"
                      step="0.00001"
                      value={reportForm.latitude}
                      onChange={handleReportChange}
                      className="w-1/2 text-sm border border-slate-200 rounded p-2"
                    />
                    <input
                      name="longitude"
                      type="number"
                      step="0.00001"
                      value={reportForm.longitude}
                      onChange={handleReportChange}
                      className="w-1/2 text-sm border border-slate-200 rounded p-2"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1 uppercase tracking-wider">
                    Photo / Video Evidence
                  </label>
                  <input
                    type="file"
                    accept="image/*,video/*"
                    onChange={handleFileChange}
                    className="w-full text-xs text-slate-500 file:mr-4 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200 file:cursor-pointer"
                  />
                  <p className="text-[10px] text-slate-400 mt-1">Upload tagged photos showing debris/blockages.</p>
                </div>

                <button
                  type="submit"
                  disabled={reportSubmitting}
                  className="w-full py-3 bg-primary hover:bg-primary/90 text-on-primary font-bold uppercase text-xs rounded-md shadow-md transition-all cursor-pointer disabled:opacity-50 tracking-wider mt-2 flex items-center justify-center gap-2"
                >
                  <Radio className="w-4 h-4 text-white animate-pulse" />
                  <span>{reportSubmitting ? 'Submitting...' : 'Log Condition & Broadcast Live Zone'}</span>
                </button>
              </form>
            </div>
          </div>

          {/* Map */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden h-[540px]">
              <div className="px-6 py-3.5 border-b border-slate-100 flex items-center justify-between">
                <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <MapPin className="h-5 w-5 text-primary-600" />
                  <span>Live Affected Impact Zone Map</span>
                </h2>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded-full border border-red-200 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse"></span>
                    {conditions.length} Active Zones
                  </span>
                  <span className="text-xs text-slate-400 font-semibold italic hidden sm:inline">Click map to target incident</span>
                </div>
              </div>
              <div className="w-full h-full relative" style={{ height: 'calc(100% - 55px)' }}>
                <MapContainer center={[24.8333, 92.7789]} zoom={11} className="w-full h-full">
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  {/* Real-time Color-Coded Incident Impact Area Layer */}
                  <IncidentImpactZoneLayer
                    conditions={conditions}
                    previewLocation={{
                      lat: reportForm.latitude,
                      lon: reportForm.longitude,
                      risk_score: reportForm.risk_score ? parseFloat(reportForm.risk_score) : (reportForm.value === 'blocked' ? 0.88 : 0.55),
                      value: reportForm.value,
                      condition_type: reportForm.condition_type,
                      radiusMeters: reportForm.radius_meters || 1400,
                    }}
                  />

                  <MapLocationInspector onLocationSelected={({ lat, lon }) => handleReportMapClick(lat, lon)} />
                </MapContainer>

                {/* Real-Time Severity Divisions Legend */}
                <IncidentSeverityLegend
                  totalIncidents={conditions.length}
                  className="absolute bottom-3 right-3 shadow-xl"
                />
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* AI Predictor tab */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* AI Settings Form */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
                <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <Cpu className="h-5 w-5 text-primary-600" />
                  <span>Disruption Risk Engine</span>
                </h2>
                <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded bg-primary-50 text-primary-700">
                  ML + Real-time
                </span>
              </div>

              {/* Assessment Mode Selector */}
              <div className="mb-4">
                <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                  Assessment Scope
                </label>
                <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-lg border border-slate-200">
                  <button
                    type="button"
                    onClick={() => {
                      setPredictMode('route');
                      setPredictResult(null);
                    }}
                    className={`py-2 px-3 rounded-md text-xs font-bold transition-all flex items-center justify-center space-x-1.5 ${
                      predictMode === 'route'
                        ? 'bg-white text-primary-700 shadow-sm border border-slate-200/60'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    <Route className="h-3.5 w-3.5" />
                    <span>Corridor Range</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setPredictMode('single');
                      setPredictResult(null);
                    }}
                    className={`py-2 px-3 rounded-md text-xs font-bold transition-all flex items-center justify-center space-x-1.5 ${
                      predictMode === 'single'
                        ? 'bg-white text-primary-700 shadow-sm border border-slate-200/60'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    <MapPin className="h-3.5 w-3.5" />
                    <span>Single Point</span>
                  </button>
                </div>
              </div>

              {predictMsg.text && (
                <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded text-xs text-red-700 flex items-center space-x-2 mb-4 font-semibold">
                  <ShieldAlert className="h-5 w-5 shrink-0" />
                  <span>{predictMsg.text}</span>
                </div>
              )}

              <form onSubmit={triggerAIPrediction} className="space-y-4">
                {predictMode === 'route' ? (
                  /* Route & Corridor Range Controls */
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-600 mb-1 uppercase tracking-wider">
                        Select Regional Arterial Lifeline
                      </label>
                      <select
                        value={selectedCorridorId}
                        onChange={(e) => handleCorridorSelect(e.target.value)}
                        className="w-full text-xs font-medium border border-slate-200 rounded p-2.5 bg-slate-50 focus:bg-white transition-colors"
                      >
                        {NER_HIGHWAY_CORRIDORS.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name} ({c.lengthKm} km)
                          </option>
                        ))}
                        <option value="custom">Custom Multi-Point Route (Map Clicked)</option>
                      </select>
                    </div>

                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <label className="block text-[10px] font-bold text-slate-500 uppercase">
                          Corridor Waypoints ({routeWaypoints.length} nodes)
                        </label>
                        <span className="text-[10px] text-primary-600 font-semibold">Click map to append</span>
                      </div>
                      <textarea
                        rows={3}
                        value={
                          customWaypointText ||
                          routeWaypoints.map((p) => `${p[0]}, ${p[1]}`).join('\n')
                        }
                        onChange={handleCustomWaypointChange}
                        placeholder="25.5788, 91.8933&#10;25.4500, 92.2000&#10;24.8333, 92.7789"
                        className="w-full text-[11px] font-mono border border-slate-200 rounded p-2 bg-slate-50 focus:bg-white"
                      />
                    </div>

                    <div>
                      <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">
                        Spatial Corridor Buffer Radius
                      </label>
                      <div className="grid grid-cols-3 gap-2">
                        {[3.0, 5.0, 10.0].map((rad) => (
                          <button
                            key={rad}
                            type="button"
                            onClick={() => setRouteBufferKm(rad)}
                            className={`py-1.5 text-xs font-bold rounded border transition-colors ${
                              routeBufferKm === rad
                                ? 'bg-primary-50 border-primary-500 text-primary-700'
                                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                            }`}
                          >
                            ± {rad} km
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Single Coordinate Controls */
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1 uppercase tracking-wider">
                      Inference Location (Lat, Lon)
                    </label>
                    <div className="flex space-x-2">
                      <input
                        name="latitude"
                        type="number"
                        step="0.00001"
                        required
                        value={aiForm.latitude}
                        onChange={handleAiChange}
                        className="w-1/2 text-sm border border-slate-200 rounded p-2"
                      />
                      <input
                        name="longitude"
                        type="number"
                        step="0.00001"
                        required
                        value={aiForm.longitude}
                        onChange={handleAiChange}
                        className="w-1/2 text-sm border border-slate-200 rounded p-2"
                      />
                    </div>
                  </div>
                )}

                <div className="flex items-center space-x-2 py-1">
                  <input
                    id="use_realtime"
                    name="use_realtime"
                    type="checkbox"
                    checked={aiForm.use_realtime}
                    onChange={handleAiChange}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-slate-300 rounded cursor-pointer"
                  />
                  <label htmlFor="use_realtime" className="text-xs font-bold text-slate-700 select-none cursor-pointer">
                    Autofetch Live Real-Time Data (Weather & DEM)
                  </label>
                </div>

                {!aiForm.use_realtime && (
                  <div className="border-t border-slate-100 pt-3 space-y-3">
                    <p className="text-[10px] text-slate-400 font-semibold mb-2">MANUAL REROUTING DRIVERS</p>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 mb-1 uppercase">24h Rainfall (mm)</label>
                        <input name="rainfall" type="number" value={aiForm.rainfall} onChange={handleAiChange} className="w-full text-xs border border-slate-200 rounded p-1.5" />
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 mb-1 uppercase">Slope Gradient (°)</label>
                        <input name="slope" type="number" value={aiForm.slope} onChange={handleAiChange} className="w-full text-xs border border-slate-200 rounded p-1.5" />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 mb-1 uppercase">Elevation (m)</label>
                        <input name="elevation" type="number" value={aiForm.elevation} onChange={handleAiChange} className="w-full text-xs border border-slate-200 rounded p-1.5" />
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 mb-1 uppercase">Soil Saturation</label>
                        <input name="soil_saturation" type="number" step="0.01" min="0" max="1" placeholder="0.2" value={aiForm.soil_saturation} onChange={handleAiChange} className="w-full text-xs border border-slate-200 rounded p-1.5" />
                      </div>
                    </div>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={predictLoading}
                  className="w-full py-3 bg-primary hover:bg-primary/90 text-on-primary font-bold uppercase text-xs rounded-md shadow-md transition-all cursor-pointer disabled:opacity-50 tracking-wider mt-2 flex items-center justify-center space-x-2"
                >
                  <Cpu className="h-4 w-4" />
                  <span>
                    {predictLoading
                      ? 'Analyzing Corridor Range...'
                      : predictMode === 'route'
                      ? 'Evaluate Route Corridor Range'
                      : 'Evaluate Coordinate Risk'}
                  </span>
                </button>
              </form>
            </div>
          </div>

          {/* AI Result Card & Geofencing Map */}
          <div className="lg:col-span-2 space-y-6">
            {predictLoading && (
              <div className="bg-white p-12 rounded-lg border border-slate-200 shadow-sm flex flex-col items-center justify-center space-y-4 h-[380px]">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
                <div className="text-center">
                  <p className="text-sm font-bold text-slate-800 tracking-wider">CRAWLING CLIMATE & DEM ENGINE</p>
                  <p className="text-xs text-slate-500 mt-2 font-medium italic animate-pulse max-w-md">{predictStep}</p>
                </div>
              </div>
            )}

            {!predictLoading && !predictResult && (
              <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden h-[480px] flex flex-col">
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                  <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                    <Navigation className="h-4 w-4 text-primary-600" />
                    <span>Predictive Corridor Geofencing Map</span>
                  </h3>
                  <span className="text-xs text-slate-400 font-semibold italic">
                    {predictMode === 'route' ? 'Click map to append route waypoints' : 'Click map to evaluate point'}
                  </span>
                </div>
                <div className="grow relative">
                  <MapContainer center={[25.18, 92.20]} zoom={8} className="w-full h-full">
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    {/* Real-time Color-Coded Incident Impact Area Layer */}
                    <IncidentImpactZoneLayer conditions={conditions} />

                    {predictMode === 'route' ? (
                      <MapClickHandler onMapClick={handleAiMapClick} />
                    ) : (
                      <MapLocationInspector
                        onLocationSelected={({ lat, lon, hazard }) => {
                          setAiForm((prev) => ({ ...prev, latitude: lat, longitude: lon }));
                          if (hazard) setPredictResult(hazard);
                        }}
                      />
                    )}

                    {predictMode === 'route' && routeWaypoints.length >= 2 && (
                      <RiskSegmentedRoute
                        routeCoordinates={routeWaypoints}
                        riskScore={0.78}
                        interactive={true}
                        label="Selected Assessment Corridor"
                      />
                    )}
                  </MapContainer>

                  {/* Real-Time Severity Divisions Legend */}
                  <IncidentSeverityLegend
                    totalIncidents={conditions.length}
                    className="absolute bottom-2 right-2 shadow-md"
                  />
                </div>
              </div>
            )}

            {predictResult && (
              <div className="space-y-6">
                {/* Check if Result is Route Range or Single Point */}
                {predictResult.route_composite_risk !== undefined ? (
                  /* Route Corridor Range Assessment Report */
                  <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-6">
                    {/* Header Banner with 3-Division Risk Styling */}
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-slate-100 pb-4 gap-3">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-extrabold uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                            Corridor Range Assessment
                          </span>
                          <span className="text-xs text-slate-400 font-semibold">
                            {predictResult.total_distance_km} km • {predictResult.range_metrics?.sample_nodes_count} sampled nodes
                          </span>
                        </div>
                        <h3 className="text-lg font-black text-slate-900 mt-1">
                          {predictResult.status_label || 'Corridor Disruption Risk Report'}
                        </h3>
                      </div>

                      {(() => {
                        const divInfo = getRiskDivision(predictResult.route_composite_risk);
                        return (
                          <div
                            className={`px-4 py-2 rounded-lg text-xs font-black uppercase text-center shadow-sm ${divInfo.badgeClass}`}
                          >
                            <div className="text-sm font-extrabold">{divInfo.percentage}% Composite Threat</div>
                            <div className="text-[10px] font-bold opacity-90">{divInfo.label}</div>
                          </div>
                        );
                      })()}
                    </div>

                    {/* Range Metrics 4-Tile Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <div className="p-3 bg-slate-50 border border-slate-200/70 rounded-lg">
                        <div className="text-[10px] font-bold text-slate-400 uppercase">Transit Distance</div>
                        <div className="text-lg font-black text-slate-800 mt-0.5">{predictResult.total_distance_km} km</div>
                      </div>
                      <div className="p-3 bg-slate-50 border border-slate-200/70 rounded-lg">
                        <div className="text-[10px] font-bold text-slate-400 uppercase">Peak 24h Rain</div>
                        <div className="text-lg font-black text-slate-800 mt-0.5">
                          {predictResult.range_metrics?.max_rainfall_mm} mm
                        </div>
                      </div>
                      <div className="p-3 bg-slate-50 border border-slate-200/70 rounded-lg">
                        <div className="text-[10px] font-bold text-slate-400 uppercase">Max Slope Incline</div>
                        <div className="text-lg font-black text-slate-800 mt-0.5">
                          {predictResult.range_metrics?.max_slope_degrees}°
                        </div>
                      </div>
                      <div className="p-3 bg-slate-50 border border-slate-200/70 rounded-lg">
                        <div className="text-[10px] font-bold text-slate-400 uppercase">Elevation Delta</div>
                        <div className="text-lg font-black text-slate-800 mt-0.5">
                          {predictResult.range_metrics?.min_elevation_m}–{predictResult.range_metrics?.max_elevation_m} m
                        </div>
                      </div>
                    </div>

                    {/* Detected Route Range Anomalies */}
                    {predictResult.detected_anomalies && predictResult.detected_anomalies.length > 0 ? (
                      <div className="space-y-3">
                        <h4 className="text-xs font-black uppercase tracking-wider text-slate-700 flex items-center space-x-1.5">
                          <AlertTriangle className="h-4 w-4 text-red-500" />
                          <span>Detected Corridor Micro-Anomalies & Threat Triggers ({predictResult.detected_anomalies.length})</span>
                        </h4>
                        <div className="space-y-2">
                          {predictResult.detected_anomalies.map((anom, idx) => (
                            <div
                              key={idx}
                              className={`p-3 rounded-lg border text-xs flex items-start justify-between space-x-3 ${
                                anom.severity === 'critical'
                                  ? 'bg-red-50 border-red-200 text-red-900'
                                  : anom.severity === 'high'
                                  ? 'bg-amber-50 border-amber-200 text-amber-900'
                                  : 'bg-yellow-50 border-yellow-200 text-yellow-900'
                              }`}
                            >
                              <div className="space-y-1">
                                <div className="font-bold flex items-center space-x-2">
                                  <span
                                    className={`h-2 w-2 rounded-full ${
                                      anom.severity === 'critical' ? 'bg-red-600 animate-ping' : 'bg-amber-500'
                                    }`}
                                  />
                                  <span>{anom.title}</span>
                                </div>
                                <p className="text-[11px] font-medium opacity-90">{anom.description}</p>
                              </div>
                              <div className="shrink-0 text-right font-mono text-[10px] font-bold">
                                <div>{anom.metric_value}</div>
                                {anom.distance_km !== undefined && (
                                  <div className="opacity-75">Km {anom.distance_km.toFixed(1)}</div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="bg-emerald-50 border border-emerald-200 p-3 rounded-lg text-xs font-semibold text-emerald-800 flex items-center space-x-2">
                        <CheckCircle className="h-4 w-4 text-emerald-600 shrink-0" />
                        <span>No severe micro-anomalies or localized trigger breaches detected along this corridor range.</span>
                      </div>
                    )}

                    {/* Hazard Sub-ranges Table */}
                    {predictResult.hazard_subranges && predictResult.hazard_subranges.length > 0 && (
                      <div className="space-y-2 border-t border-slate-100 pt-4">
                        <h4 className="text-xs font-black uppercase tracking-wider text-slate-500">
                          Contiguous Hazard Sub-ranges
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                          {predictResult.hazard_subranges.map((seg, sIdx) => {
                            const segDiv = getRiskDivision(seg.risk_score);
                            return (
                              <div
                                key={sIdx}
                                className={`p-2.5 rounded-md border text-xs flex items-center justify-between ${segDiv.badgeClass}`}
                              >
                                <div>
                                  <div className="font-bold">Segment {seg.segment_index}</div>
                                  <div className="text-[10px] opacity-80">
                                    Km {seg.start_km.toFixed(0)} → Km {seg.end_km.toFixed(0)}
                                  </div>
                                </div>
                                <div className="font-extrabold text-sm">{Math.round(seg.risk_score * 100)}%</div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Map Display with 3-Division Segmented Polyline */}
                    <div className="border border-slate-200 rounded-lg overflow-hidden h-[340px] relative">
                      <MapContainer center={[25.18, 92.20]} zoom={8} className="w-full h-full">
                        <TileLayer
                          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />

                        {/* Real-time Color-Coded Incident Impact Area Layer */}
                        <IncidentImpactZoneLayer conditions={conditions} />

                        {/* Evaluated Route with 3-Tier Risk Divisions */}
                        <RiskSegmentedRoute
                          routeCoordinates={routeWaypoints}
                          riskScore={predictResult.route_composite_risk}
                          interactive={true}
                          label="Evaluated Corridor Range"
                        />

                        {/* Anomaly Callout Markers */}
                        {predictResult.detected_anomalies?.map((anom, aIdx) => {
                          if (!anom.latitude || !anom.longitude) return null;
                          return (
                            <Marker
                              key={`anom-${aIdx}`}
                              position={[anom.latitude, anom.longitude]}
                            >
                              <Popup>
                                <div className="text-xs p-1">
                                  <div className="font-bold text-red-600 uppercase">{anom.title}</div>
                                  <div className="mt-0.5">{anom.description}</div>
                                  <div className="text-[10px] text-slate-500 mt-1 font-mono">{anom.metric_value}</div>
                                </div>
                              </Popup>
                            </Marker>
                          );
                        })}
                      </MapContainer>

                      <RiskLegendControl compact={true} className="absolute bottom-2 right-2 shadow-md" />
                    </div>
                  </div>
                ) : (
                  /* Single Point Coordinate Report */
                  <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-6">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4">
                      <div>
                        <h3 className="text-lg font-bold text-slate-900">AI Hazard Classifier Report</h3>
                        <p className="text-xs text-slate-500 font-medium mt-0.5">
                          Evaluated on {new Date().toLocaleDateString()} at {predictResult.latitude}, {predictResult.longitude}
                        </p>
                      </div>
                      {(() => {
                        const divInfo = getRiskDivision(predictResult.risk_score);
                        return (
                          <div
                            className={`mt-2 sm:mt-0 px-4 py-1.5 rounded-full text-xs font-black uppercase text-center ${divInfo.badgeClass}`}
                          >
                            {predictResult.risk_level} Risk ({Math.round(predictResult.risk_score * 100)}%)
                          </div>
                        );
                      })()}
                    </div>

                    <div className="bg-slate-50 p-4 rounded-md border border-slate-200">
                      <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-500 mb-1">Explainable AI Driver Details</h4>
                      <p className="text-sm font-medium text-slate-800 leading-relaxed">
                        {predictResult.explanation}
                      </p>
                    </div>

                    <div>
                      <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-500 mb-3">Model Input Features</h4>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                        <div className="p-3 bg-white border border-slate-100 rounded shadow-sm">
                          <div className="text-[10px] font-bold text-slate-400 uppercase">24h Rainfall</div>
                          <div className="text-base font-extrabold text-slate-800 mt-0.5">{predictResult.features?.rainfall_mm} mm</div>
                        </div>
                        <div className="p-3 bg-white border border-slate-100 rounded shadow-sm">
                          <div className="text-[10px] font-bold text-slate-400 uppercase">Slope Gradient</div>
                          <div className="text-base font-extrabold text-slate-800 mt-0.5">{predictResult.features?.slope_degrees}°</div>
                        </div>
                        <div className="p-3 bg-white border border-slate-100 rounded shadow-sm">
                          <div className="text-[10px] font-bold text-slate-400 uppercase">Elevation (DEM)</div>
                          <div className="text-base font-extrabold text-slate-800 mt-0.5">{predictResult.features?.elevation_m} m</div>
                        </div>
                        <div className="p-3 bg-white border border-slate-100 rounded shadow-sm">
                          <div className="text-[10px] font-bold text-slate-400 uppercase">Soil Saturation</div>
                          <div className="text-base font-extrabold text-slate-800 mt-0.5">{Math.round((predictResult.features?.soil_saturation || 0) * 100)}%</div>
                        </div>
                        <div className="p-3 bg-white border border-slate-100 rounded shadow-sm">
                          <div className="text-[10px] font-bold text-slate-400 uppercase">Runoff Drainage</div>
                          <div className="text-base font-extrabold text-slate-800 mt-0.5">{predictResult.features?.drainage_quality}</div>
                        </div>
                        <div className="p-3 bg-white border border-slate-100 rounded shadow-sm">
                          <div className="text-[10px] font-bold text-slate-400 uppercase">Vegetation NDVI</div>
                          <div className="text-base font-extrabold text-slate-800 mt-0.5">{predictResult.features?.vegetation_cover}</div>
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-between items-center text-[10px] text-slate-400 font-bold border-t pt-4">
                      <span>Engine: Scikit-Learn Gradient Boosting</span>
                      <span>Model version: {predictResult.model_version}</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

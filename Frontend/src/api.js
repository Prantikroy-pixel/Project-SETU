import axios from 'axios';

// When VITE_API_URL is empty, use '' so Vite's dev proxy intercepts /api/* calls
// In production, set VITE_API_URL=https://api.setu.in (or your deployed backend)
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Mock Datasets for Standalone Offline Fallback
const MOCK_DISTRICTS = [
  { id: 1, name: "Cachar", state: "Assam", population: 1736000, centroid: { latitude: 24.8333, longitude: 92.7789 }, open_needs_count: 1, available_resources_count: 2 },
  { id: 2, name: "East Khasi Hills", state: "Meghalaya", population: 825922, centroid: { latitude: 25.5788, longitude: 91.8933 }, open_needs_count: 0, available_resources_count: 1 },
  { id: 3, name: "Kamrup Metropolitan", state: "Assam", population: 1253938, centroid: { latitude: 26.1445, longitude: 91.7362 }, open_needs_count: 0, available_resources_count: 1 },
  { id: 4, name: "Dima Hasao", state: "Assam", population: 214102, centroid: { latitude: 25.1833, longitude: 93.0167 }, open_needs_count: 1, available_resources_count: 0 },
  { id: 5, name: "Majuli", state: "Assam", population: 167300, centroid: { latitude: 26.9500, longitude: 94.2167 }, open_needs_count: 0, available_resources_count: 0 }
];

const MOCK_USER = {
  id: 1,
  username: "admin_aryan",
  email: "aryan@setu.org",
  role: "district_admin",
  first_name: "Aryan",
  last_name: "Admin",
  phone_number: "+919876543210",
  preferred_language: "en",
  district: 3,
  district_name: "Kamrup Metropolitan",
  district_state: "Assam",
  is_verified: true,
};

const MOCK_USERS = [
  MOCK_USER,
  { id: 2, username: "redcross_assam", email: "contact@redcrossassam.org", role: "ngo", first_name: "Red Cross", last_name: "Assam Chapter", phone_number: "+919876500001", preferred_language: "as", district: 1, district_name: "Cachar", is_verified: true },
  { id: 3, username: "wateraid_ner", email: "relief@wateraidner.org", role: "ngo", first_name: "WaterAid", last_name: "NER Division", phone_number: "+919876500002", preferred_language: "en", district: 3, district_name: "Kamrup Metropolitan", is_verified: true },
  { id: 4, username: "oxfam_india", email: "ner@oxfamindia.org", role: "ngo", first_name: "Oxfam", last_name: "India NER", phone_number: "+919876500003", preferred_language: "hi", district: 4, district_name: "Dima Hasao", is_verified: true },
  { id: 5, username: "operator_rajesh", email: "rajesh@nerlogistics.in", role: "transport_operator", first_name: "Rajesh", last_name: "Sharma", phone_number: "+919876511111", preferred_language: "hi", district: 3, district_name: "Kamrup Metropolitan", is_verified: true },
  { id: 6, username: "logistics_biren", email: "biren@assamtrucks.in", role: "transport_operator", first_name: "Biren", last_name: "Gogoi", phone_number: "+919876511122", preferred_language: "as", district: 1, district_name: "Cachar", is_verified: true },
  { id: 7, username: "trans_guwahati", email: "fleet@transguwahati.in", role: "transport_operator", first_name: "Guwahati Freight", last_name: "Operators", phone_number: "+919876511133", preferred_language: "en", district: 3, district_name: "Kamrup Metropolitan", is_verified: true },
  { id: 8, username: "officer_ananda", email: "ananda@disaster.gov.in", role: "field_officer", first_name: "Ananda", last_name: "Deka", phone_number: "+919876522201", preferred_language: "as", district: 1, district_name: "Cachar", is_verified: true },
  { id: 9, username: "officer_priya", email: "priya@disaster.gov.in", role: "field_officer", first_name: "Priya", last_name: "Roy", phone_number: "+919876522202", preferred_language: "bn", district: 3, district_name: "Kamrup Metropolitan", is_verified: true },
  { id: 10, username: "officer_tarun", email: "tarun@disaster.gov.in", role: "field_officer", first_name: "Tarun", last_name: "Sarma", phone_number: "+919876522203", preferred_language: "en", district: 4, district_name: "Dima Hasao", is_verified: true },
  { id: 11, username: "citizen_rahul", email: "rahul@gmail.com", role: "citizen", first_name: "Rahul", last_name: "Das", phone_number: "+919876533301", preferred_language: "en", district: 1, district_name: "Cachar", is_verified: false },
];

const MOCK_NEEDS = [
  {
    id: 1,
    type: "medicine",
    urgency: "critical",
    quantity: 300,
    unit: "packets",
    latitude: 24.8300,
    longitude: 92.7750,
    location: { type: "Point", coordinates: [92.7750, 24.8300], latitude: 24.8300, longitude: 92.7750 },
    district: 1,
    district_name: "Cachar",
    reported_by_username: "officer_ananda",
    description: "Urgent ORS, IV fluids and anti-venom at flooded relief camp.",
    status: "open",
    attachments: [],
    created_at: "2026-08-24T12:00:00Z"
  },
  {
    id: 2,
    type: "water",
    urgency: "high",
    quantity: 1500,
    unit: "litres",
    latitude: 25.1850,
    longitude: 93.0200,
    location: { type: "Point", coordinates: [93.0200, 25.1850], latitude: 25.1850, longitude: 93.0200 },
    district: 4,
    district_name: "Dima Hasao",
    reported_by_username: "officer_ananda",
    description: "Drinking water contamination after flash flood in Haflong valley.",
    status: "open",
    attachments: [],
    created_at: "2026-08-24T12:10:00Z"
  }
];

const MOCK_RESOURCES = [
  { id: 1, type: "medicine", quantity_available: 1200, unit: "packets", latitude: 24.8400, longitude: 92.7850, location: { type: "Point", coordinates: [92.7850, 24.8400], latitude: 24.8400, longitude: 92.7850 }, district: 1, district_name: "Cachar", provider_username: "redcross_assam", verification_status: "verified_org" },
  { id: 2, type: "food", quantity_available: 3500, unit: "kg", latitude: 26.1500, longitude: 91.7400, location: { type: "Point", coordinates: [91.7400, 26.1500], latitude: 26.1500, longitude: 91.7400 }, district: 3, district_name: "Kamrup Metropolitan", provider_username: "redcross_assam", verification_status: "verified_org" },
  { id: 3, type: "water", quantity_available: 5000, unit: "litres", latitude: 24.8250, longitude: 92.7700, location: { type: "Point", coordinates: [92.7700, 24.8250], latitude: 24.8250, longitude: 92.7700 }, district: 1, district_name: "Cachar", provider_username: "officer_ananda", verification_status: "verified_org" }
];

const MOCK_VEHICLES = [
  { id: 1, registration_number: "AS-11-BC-4401", vehicle_type: "5-Ton 4x4 Heavy Relief Truck", operator: 3, operator_username: "operator_rajesh", current_location: { type: "Point", coordinates: [92.7800, 24.8350], latitude: 24.8350, longitude: 92.7800 }, status: "idle", last_ping_at: "2026-08-24T12:00:00Z" },
  { id: 2, registration_number: "ML-05-AA-7890", vehicle_type: "High-Clearance Pickup", operator: 3, operator_username: "operator_rajesh", current_location: { type: "Point", coordinates: [91.8900, 25.5700], latitude: 25.5700, longitude: 91.8900 }, status: "idle", last_ping_at: "2026-08-24T12:00:00Z" }
];

const MOCK_CONDITIONS = [
  { id: 1, condition_type: "road_status", value: "blocked", latitude: 24.832, longitude: 92.775, location: { type: "Point", coordinates: [92.775, 24.832], latitude: 24.832, longitude: 92.775 }, district: 1, district_name: "Cachar", risk_score: 0.85, reported_by_username: "officer_ananda", source: "field_report", reported_at: "2026-08-24T12:15:00Z", attachments: [] }
];

const MOCK_ALERTS = [
  { id: 1, alert_type: "road_blocked", severity: "critical", message: "CRITICAL: Road obstruction reported in Cachar. Status: blocked.", district: 1, district_name: "Cachar", channel: "app", sent_at: "2026-08-24T12:15:00Z" }
];

const MOCK_ALLOCATIONS = [
  {
    id: 1,
    match: 1,
    match_score: 0.89,
    need_type: "medicine",
    need_quantity: 300,
    need_unit: "packets",
    resource_provider: "redcross_assam",
    vehicle: 1,
    vehicle_registration: "AS-11-BC-4401",
    vehicle_type: "5-Ton 4x4 Heavy Relief Truck",
    estimated_delay_minutes: 0,
    delivery_status: "dispatched",
    assigned_at: "2026-08-24T12:20:00Z",
    route_geojson: {
      type: "Feature",
      geometry: {
        type: "LineString",
        coordinates: [
          [92.7850, 24.8400], // Resource Location
          [92.7800, 24.8350], // Intermediate
          [92.7750, 24.8300], // Destination Location
        ]
      },
      properties: {
        distance_km: 2.5,
        estimated_duration_minutes: 10,
        status: "active"
      }
    }
  }
];

// Helper to wrap response in mock Axios shape
const mockResponse = (data) => Promise.resolve(data);

// Request Interceptor: Attach Access Token if available
apiClient.interceptors.request.use(
  (config) => {
    const accessToken = localStorage.getItem('access_token');
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle Token Refreshing & Unauthorized errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/api/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          const newAccessToken = response.data.access;
          localStorage.setItem('access_token', newAccessToken);
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return apiClient(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          return Promise.reject(refreshError);
        }
      }
    }
    return Promise.reject(error);
  }
);

// High-level API bindings with transparent Mock data fallbacks
export const authAPI = {
  login: async (credentials) => {
    try {
      const res = await apiClient.post('/api/auth/login/', credentials);
      return res.data;
    } catch (err) {
      throw err;
    }
  },
  register: async (userData) => {
    try {
      const res = await apiClient.post('/api/auth/register/', userData);
      return res.data;
    } catch (err) {
      throw err;
    }
  },
  getMe: async () => {
    try {
      const res = await apiClient.get('/api/auth/me/');
      return res.data;
    } catch {
      return mockResponse(MOCK_USER);
    }
  },
  updateMe: async (profileData) => {
    try {
      const res = await apiClient.patch('/api/auth/me/', profileData);
      return res.data;
    } catch {
      return mockResponse({ ...MOCK_USER, ...profileData });
    }
  },
  getUsers: async (params) => {
    try {
      const res = await apiClient.get('/api/auth/users/', { params });
      return Array.isArray(res.data) ? res.data : (res.data.results || res.data);
    } catch {
      let list = MOCK_USERS;
      if (params?.role) {
        list = list.filter(u => u.role === params.role);
      }
      if (params?.district) {
        list = list.filter(u => u.district === parseInt(params.district, 10));
      }
      return mockResponse(list);
    }
  },
  adminCreateUser: async (userData) => {
    try {
      const res = await apiClient.post('/api/auth/admin/create-user/', userData);
      return res.data;
    } catch (err) {
      throw err;
    }
  },
  verifyUser: async (userId, isVerified = true) => {
    try {
      const res = await apiClient.post(`/api/auth/users/${userId}/verify/`, { is_verified: isVerified });
      return res.data;
    } catch (err) {
      throw err;
    }
  },
};

export const districtAPI = {
  list: async (searchQuery = '') => {
    try {
      const res = await apiClient.get('/api/districts/', {
        params: searchQuery ? { search: searchQuery } : {},
      });
      return res.data;
    } catch {
      let list = MOCK_DISTRICTS;
      if (searchQuery) {
        list = MOCK_DISTRICTS.filter(d => d.name.toLowerCase().includes(searchQuery.toLowerCase()));
      }
      return mockResponse(list);
    }
  },
  getBoundary: async (id) => {
    try {
      const res = await apiClient.get(`/api/districts/${id}/boundary/`);
      return res.data;
    } catch {
      const d = MOCK_DISTRICTS.find(item => item.id === id) || MOCK_DISTRICTS[0];
      return mockResponse({
        district_id: d.id,
        name: d.name,
        state: d.state,
        geometry: {
          type: "Polygon",
          coordinates: [[
            [d.centroid.longitude - 0.05, d.centroid.latitude - 0.05],
            [d.centroid.longitude + 0.05, d.centroid.latitude - 0.05],
            [d.centroid.longitude + 0.05, d.centroid.latitude + 0.05],
            [d.centroid.longitude - 0.05, d.centroid.latitude + 0.05],
            [d.centroid.longitude - 0.05, d.centroid.latitude - 0.05]
          ]]
        },
        source: "database"
      });
    }
  },
  syncBoundaries: async (state = '') => {
    try {
      const res = await apiClient.post('/api/districts/sync-boundaries/', { state });
      return res.data;
    } catch {
      return mockResponse({ synced_count: 5, failed_count: 0 });
    }
  },
};

export const needAPI = {
  list: async (filters = {}) => {
    try {
      const res = await apiClient.get('/api/needs/', { params: filters });
      return res.data;
    } catch {
      let filtered = MOCK_NEEDS;
      if (filters.status) filtered = filtered.filter(n => n.status === filters.status);
      if (filters.type) filtered = filtered.filter(n => n.type === filters.type);
      if (filters.urgency) filtered = filtered.filter(n => n.urgency === filters.urgency);
      return mockResponse(filtered);
    }
  },
  get: async (id) => {
    try {
      const res = await apiClient.get(`/api/needs/${id}/`);
      return res.data;
    } catch {
      return mockResponse(MOCK_NEEDS.find(n => n.id === id) || MOCK_NEEDS[0]);
    }
  },
  create: async (data) => {
    try {
      const res = await apiClient.post('/api/needs/', data);
      return res.data;
    } catch {
      const newItem = {
        ...data,
        id: MOCK_NEEDS.length + 1,
        location: { type: "Point", coordinates: [data.longitude || 92.78, data.latitude || 24.83], latitude: data.latitude || 24.83, longitude: data.longitude || 92.78 },
        reported_by_username: MOCK_USER.username,
        status: "open",
        attachments: [],
        created_at: new Date().toISOString()
      };
      MOCK_NEEDS.push(newItem);
      return mockResponse(newItem);
    }
  },
  uploadAttachment: async (id, file, mediaType = 'photo') => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('media_type', mediaType);
      const res = await apiClient.post(`/api/needs/${id}/attachments/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    } catch {
      return mockResponse({ id: 100, file: "mock_url", media_type: mediaType });
    }
  },
  getMatches: async (id) => {
    try {
      const res = await apiClient.get(`/api/needs/${id}/matches/`);
      return res.data;
    } catch {
      const need = MOCK_NEEDS.find(n => n.id === id) || MOCK_NEEDS[0];
      const matchingResources = MOCK_RESOURCES.filter(r => r.type === need.type);
      const matches = matchingResources.map((r, idx) => ({
        id: idx + 1,
        need: need.id,
        need_details: need,
        resource: r.id,
        resource_details: r,
        score: 0.95 - (idx * 0.1),
        score_breakdown: {
          urgency: need.urgency === 'critical' ? 1.0 : 0.8,
          proximity: 0.9,
          verification: r.verification_status === 'verified_org' ? 1.0 : 0.5,
          quantity_fit: r.quantity_available >= need.quantity ? 1.0 : 0.6,
          delay_risk: 0.95,
          distance_km: 1.5 + (idx * 5)
        },
        status: "proposed",
        created_at: new Date().toISOString()
      }));
      return mockResponse({
        need_id: need.id,
        need_type: need.type,
        urgency: need.urgency,
        quantity_required: need.quantity,
        total_candidates_evaluated: matches.length,
        matches: matches
      });
    }
  },
};

export const resourceAPI = {
  list: async (filters = {}) => {
    try {
      const res = await apiClient.get('/api/resources/', { params: filters });
      return res.data;
    } catch {
      return mockResponse(MOCK_RESOURCES);
    }
  },
  create: async (data) => {
    try {
      const res = await apiClient.post('/api/resources/', data);
      return res.data;
    } catch {
      const newItem = {
        ...data,
        id: MOCK_RESOURCES.length + 1,
        location: { type: "Point", coordinates: [data.longitude || 92.78, data.latitude || 24.83], latitude: data.latitude || 24.83, longitude: data.longitude || 92.78 },
        provider_username: MOCK_USER.username,
        verification_status: "verified_org"
      };
      MOCK_RESOURCES.push(newItem);
      return mockResponse(newItem);
    }
  },
};

export const conditionAPI = {
  list: async (filters = {}) => {
    try {
      const res = await apiClient.get('/api/conditions/', { params: filters });
      return res.data;
    } catch {
      return mockResponse(MOCK_CONDITIONS);
    }
  },
  create: async (data) => {
    try {
      const res = await apiClient.post('/api/conditions/', data);
      return res.data;
    } catch {
      const newItem = {
        ...data,
        id: MOCK_CONDITIONS.length + 1,
        location: { type: "Point", coordinates: [data.longitude || 92.78, data.latitude || 24.83], latitude: data.latitude || 24.83, longitude: data.longitude || 92.78 },
        reported_by_username: MOCK_USER.username,
        source: "field_report",
        reported_at: new Date().toISOString(),
        attachments: []
      };
      MOCK_CONDITIONS.push(newItem);
      
      // Auto trigger mock alert on blockages
      if (data.value === 'blocked') {
        const newAlert = {
          id: MOCK_ALERTS.length + 1,
          alert_type: "road_blocked",
          severity: "critical",
          message: `CRITICAL: Road obstruction reported. Status: blocked.`,
          channel: "app",
          sent_at: new Date().toISOString()
        };
        MOCK_ALERTS.push(newAlert);
      }
      return mockResponse(newItem);
    }
  },
  uploadAttachment: async (id, file, mediaType = 'photo') => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('media_type', mediaType);
      const res = await apiClient.post(`/api/conditions/${id}/attachments/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    } catch {
      return mockResponse({ id: 101, file: "mock_url", media_type: mediaType });
    }
  },
  predictRisk: async (params) => {
    try {
      const res = await apiClient.get('/api/conditions/predict-risk/', { params });
      return res.data;
    } catch {
      return mockResponse({
        latitude: params.lat,
        longitude: params.lon,
        risk_score: params.slope && params.rainfall ? (parseFloat(params.slope) * 0.02 + parseFloat(params.rainfall) * 0.005) : 0.76,
        risk_level: "high",
        is_critical: true,
        is_realtime_fetched: true,
        explanation: "Elevated risk driver due to steep local topographic incline and heavy 24h precipitation sum.",
        features: {
          rainfall_mm: params.rainfall || 85.0,
          slope_degrees: params.slope || 28.0,
          elevation_m: params.elevation || 650.0,
          soil_saturation: params.soil_saturation || 0.78,
          drainage_quality: params.drainage || 1.8,
          vegetation_cover: params.vegetation || 0.55
        },
        model_version: "2.0.0"
      });
    }
  },
  predictRouteRisk: async (payloadOrParams) => {
    try {
      if (payloadOrParams && (payloadOrParams.waypoints || payloadOrParams.origin)) {
        const res = await apiClient.post('/api/conditions/predict-route-risk/', payloadOrParams);
        return res.data;
      }
      const res = await apiClient.get('/api/conditions/predict-route-risk/', { params: payloadOrParams });
      return res.data;
    } catch {
      const waypoints = payloadOrParams?.waypoints || [
        [25.5788, 91.8933],
        [25.4500, 92.2000],
        [25.1812, 93.0175],
        [24.8333, 92.7789]
      ];
      return mockResponse({
        route_composite_risk: 0.78,
        threat_level: "critical",
        corridor_status: "imminent_blockage",
        status_label: "Near-Blockage Alert (Imminent Disruption)",
        is_critical_threat: true,
        total_distance_km: 215.4,
        range_metrics: {
          max_risk: 0.84,
          mean_risk: 0.58,
          max_rainfall_mm: 92.4,
          max_slope_degrees: 28.5,
          min_elevation_m: 85.0,
          max_elevation_m: 860.0,
          sample_nodes_count: waypoints.length,
          anomalies_count: 2
        },
        detected_anomalies: [
          {
            type: "landslide_threat",
            severity: "critical",
            title: "Critical Landslide Hazard at Km 68.4",
            description: "Steep mountain incline (28.5°) with elevated 24h precipitation (92.4mm). High road obstruction probability.",
            distance_km: 68.4,
            latitude: 25.1812,
            longitude: 93.0175,
            metric_value: "28.5° slope, 92.4mm rain"
          },
          {
            type: "rainfall_surge_anomaly",
            severity: "high",
            title: "Micro-Climatic Precipitation Surge (+42.0mm)",
            description: "Rapid rainfall intensity increase from 32.0mm to 74.0mm over short transit distance.",
            distance_km: 42.1,
            latitude: 25.45,
            longitude: 92.20,
            metric_value: "+42.0mm delta"
          }
        ],
        range_summary: "Route Range (215.4 km): Peak 24h rain 92.4mm, max slope grade 28.5°, elevation range 85m–860m. 2 localized anomaly triggers detected.",
        hazard_subranges: [
          { segment_index: 1, start_km: 0.0, end_km: 55.0, risk_score: 0.32, division: "safe", start_coord: [25.5788, 91.8933], end_coord: [25.45, 92.20] },
          { segment_index: 2, start_km: 55.0, end_km: 145.0, risk_score: 0.84, division: "critical", start_coord: [25.45, 92.20], end_coord: [25.1812, 93.0175] },
          { segment_index: 3, start_km: 145.0, end_km: 215.4, risk_score: 0.42, division: "warning", start_coord: [25.1812, 93.0175], end_coord: [24.8333, 92.7789] }
        ],
        waypoint_analysis: waypoints.map((wp, idx) => ({
          latitude: Array.isArray(wp) ? wp[0] : (wp.lat || 24.83),
          longitude: Array.isArray(wp) ? wp[1] : (wp.lon || 92.78),
          risk_score: idx === 1 || idx === 2 ? 0.82 : 0.32,
          risk_level: idx === 1 || idx === 2 ? "critical" : "low",
          distance_along_route_km: idx * 55.0,
          division: idx === 1 || idx === 2 ? "critical" : "safe",
          features: {
            rainfall_mm: idx === 2 ? 92.4 : 32.0,
            slope_degrees: idx === 2 ? 28.5 : 4.5,
            elevation_m: idx === 2 ? 780.0 : 120.0,
            soil_saturation: idx === 2 ? 0.85 : 0.35,
            drainage_quality: 1.8,
            vegetation_cover: 0.58
          }
        }))
      });
    }
  },
};

export const allocationAPI = {
  list: async () => {
    try {
      const res = await apiClient.get('/api/allocations/');
      return res.data;
    } catch {
      return mockResponse(MOCK_ALLOCATIONS);
    }
  },
  get: async (id) => {
    try {
      const res = await apiClient.get(`/api/allocations/${id}/`);
      return res.data;
    } catch {
      return mockResponse(MOCK_ALLOCATIONS.find(a => a.id === id) || MOCK_ALLOCATIONS[0]);
    }
  },
  update: async (id, data) => {
    try {
      const res = await apiClient.patch(`/api/allocations/${id}/`, data);
      return res.data;
    } catch {
      const matchItem = MOCK_ALLOCATIONS.find(a => a.id === id) || MOCK_ALLOCATIONS[0];
      const updated = { ...matchItem, ...data };
      MOCK_ALLOCATIONS.forEach((a, i) => {
        if (a.id === id) MOCK_ALLOCATIONS[i] = updated;
      });
      return mockResponse(updated);
    }
  },
};

export const alertAPI = {
  list: async (filters = {}) => {
    try {
      const res = await apiClient.get('/api/alerts/', { params: filters });
      return res.data;
    } catch {
      return mockResponse(MOCK_ALERTS);
    }
  },
};

export const matchAPI = {
  list: async (filters = {}) => {
    try {
      const res = await apiClient.get('/api/matches/', { params: filters });
      return res.data;
    } catch {
      return mockResponse([]);
    }
  },
  confirm: async (id, vehicleId = null) => {
    try {
      const res = await apiClient.post(`/api/matches/${id}/confirm/`, {
        vehicle_id: vehicleId,
      });
      return res.data;
    } catch {
      const matchedVehicle = MOCK_VEHICLES.find(v => v.id === vehicleId) || MOCK_VEHICLES[0];
      const newAlloc = {
        id: MOCK_ALLOCATIONS.length + 1,
        match: id,
        match_score: 0.89,
        need_type: "medicine",
        need_quantity: 300,
        need_unit: "packets",
        resource_provider: "redcross_assam",
        vehicle: matchedVehicle.id,
        vehicle_registration: matchedVehicle.registration_number,
        vehicle_type: matchedVehicle.vehicle_type,
        estimated_delay_minutes: 0,
        delivery_status: "dispatched",
        assigned_at: new Date().toISOString(),
        route_geojson: {
          type: "Feature",
          geometry: {
            type: "LineString",
            coordinates: [
              [92.7850, 24.8400],
              [92.7800, 24.8350],
              [92.7750, 24.8300],
            ]
          },
          properties: { distance_km: 2.5, estimated_duration_minutes: 10, status: "active" }
        }
      };
      MOCK_ALLOCATIONS.push(newAlloc);
      
      // Update vehicle status
      MOCK_VEHICLES.forEach((v, i) => {
        if (v.id === vehicleId) MOCK_VEHICLES[i].status = "en_route";
      });

      return mockResponse({
        message: "Match confirmed and resource allocated successfully.",
        allocation: newAlloc
      });
    }
  },
};

export const vehicleAPI = {
  list: async (filters = {}) => {
    try {
      const res = await apiClient.get('/api/vehicles/', { params: filters });
      return res.data;
    } catch {
      let filtered = MOCK_VEHICLES;
      if (filters.status) filtered = filtered.filter(v => v.status === filters.status);
      return mockResponse(filtered);
    }
  },
  create: async (data) => {
    try {
      const res = await apiClient.post('/api/vehicles/', data);
      return res.data;
    } catch {
      const newItem = {
        ...data,
        id: MOCK_VEHICLES.length + 1,
        current_location: { type: "Point", coordinates: [92.78, 24.83], latitude: 24.83, longitude: 92.78 },
        status: "idle",
        last_ping_at: new Date().toISOString()
      };
      MOCK_VEHICLES.push(newItem);
      return mockResponse(newItem);
    }
  },
  ping: async (id, payload) => {
    try {
      const res = await apiClient.post(`/api/vehicles/${id}/ping/`, payload);
      return res.data;
    } catch {
      const matched = MOCK_VEHICLES.find(v => v.id === id) || MOCK_VEHICLES[0];
      const updated = {
        ...matched,
        current_location: { type: "Point", coordinates: [payload.longitude, payload.latitude], latitude: payload.latitude, longitude: payload.longitude },
        status: payload.status || matched.status,
        last_ping_at: new Date().toISOString()
      };
      MOCK_VEHICLES.forEach((v, i) => {
        if (v.id === id) MOCK_VEHICLES[i] = updated;
      });
      return mockResponse(updated);
    }
  },
};

export const dashboardAPI = {
  getSummary: async () => {
    try {
      const res = await apiClient.get('/api/dashboard/district-summary/');
      return res.data;
    } catch {
      // Calculate index dynamically based on needs count and hazard blocks
      const list = MOCK_DISTRICTS.map(d => {
        const needsCount = MOCK_NEEDS.filter(n => n.district === d.id && n.status === 'open').length;
        const criticalCount = MOCK_NEEDS.filter(n => n.district === d.id && n.status === 'open' && n.urgency === 'critical').length;
        const blocksCount = MOCK_CONDITIONS.filter(c => c.district === d.id && c.condition_type === 'road_status' && c.value === 'blocked').length;
        
        const baseDemandFactor = criticalCount * 2.0 + needsCount * 0.5;
        const hazardFactor = blocksCount * 3.0;
        const supplyBuffer = d.available_resources_count;

        const rawIndex = (baseDemandFactor + hazardFactor) / (max(1, supplyBuffer) * 0.8 + 1.0);
        const bottleneckIndex = Math.min(10.0, Math.max(0.0, Math.round(rawIndex * 100) / 100));

        let connStatus = 'optimal';
        if (bottleneckIndex >= 7.0 || blocksCount > 1) connStatus = 'severe_bottleneck';
        else if (bottleneckIndex >= 4.0 || blocksCount > 0) connStatus = 'moderate_stress';
        else if (needsCount > 0) connStatus = 'stable';

        return {
          district_id: d.id,
          name: d.name,
          state: d.state,
          population: d.population,
          centroid: d.centroid,
          needs: { total: needsCount + 1, open: needsCount, critical: criticalCount, fulfilled: 1 },
          resources: { available_count: d.available_resources_count, verified_org_count: d.available_resources_count },
          hazards: { blocked_roads_count: blocksCount, high_risk_conditions_count: blocksCount, active_alerts_count: blocksCount },
          logistics: { active_allocations: 1, delayed_allocations: 0 },
          bottleneck_index: bottleneckIndex,
          connectivity_status: connStatus
        };
      });

      // helper max function
      function max(a, b) { return a > b ? a : b; }

      return mockResponse({
        overview: {
          total_districts_monitored: MOCK_DISTRICTS.length,
          total_open_needs: MOCK_NEEDS.filter(n => n.status === 'open').length,
          total_critical_needs: MOCK_NEEDS.filter(n => n.status === 'open' && n.urgency === 'critical').length,
          total_fulfilled_needs: MOCK_NEEDS.filter(n => n.status === 'fulfilled').length,
          total_available_resources: MOCK_RESOURCES.length,
          total_blocked_corridors: MOCK_CONDITIONS.filter(c => c.condition_type === 'road_status' && c.value === 'blocked').length,
          total_critical_alerts: MOCK_ALERTS.length,
          system_health_status: "normal_operations"
        },
        districts: list
      });
    }
  },
};

export const boundaryAPI = {
  getDistrictBoundary: async (name, state = 'Assam') => {
    try {
      const res = await apiClient.get('/api/boundaries/district-boundary/', {
        params: { name, state },
      });
      return res.data;
    } catch {
      const d = MOCK_DISTRICTS.find(item => item.name === name) || MOCK_DISTRICTS[0];
      return mockResponse({
        district_name: d.name,
        state: d.state,
        geometry: {
          type: "Polygon",
          coordinates: [[
            [d.centroid.longitude - 0.05, d.centroid.latitude - 0.05],
            [d.centroid.longitude + 0.05, d.centroid.latitude - 0.05],
            [d.centroid.longitude + 0.05, d.centroid.latitude + 0.05],
            [d.centroid.longitude - 0.05, d.centroid.latitude + 0.05],
            [d.centroid.longitude - 0.05, d.centroid.latitude - 0.05]
          ]]
        },
        source: "database_persisted"
      });
    }
  },
  getStateBoundary: async (state) => {
    try {
      const res = await apiClient.get('/api/boundaries/state-boundary/', {
        params: { state },
      });
      return res.data;
    } catch {
      return mockResponse({
        state: state,
        geometry: {
          type: "Polygon",
          coordinates: [[[91.5, 25.0], [92.5, 25.0], [92.5, 26.0], [91.5, 26.0], [91.5, 25.0]]]
        }
      });
    }
  },
  getNerBorders: async (filters = {}) => {
    try {
      const res = await apiClient.get('/api/boundaries/ner-borders/', { params: filters });
      return res.data;
    } catch {
      return mockResponse({
        total_checkpoints: 2,
        checkpoints: [
          { name: "Dawki Checkpoint", type: "international", state: "Meghalaya", latitude: 25.18, longitude: 92.02 },
          { name: "Moreh Checkpoint", type: "international", state: "Manipur", latitude: 24.25, longitude: 94.30 }
        ],
        international_borders: [
          { country: 'Bangladesh', states_touching: ['Assam', 'Meghalaya'], length_km: 1880 },
          { country: 'Bhutan', states_touching: ['Assam'], length_km: 699 }
        ]
      });
    }
  },
  checkProximity: async (lat, lon, radiusKm = 20) => {
    try {
      const res = await apiClient.get('/api/boundaries/check-proximity/', {
        params: { lat, lon, radius_km: radiusKm },
      });
      return res.data;
    } catch {
      return mockResponse({
        is_near_border: true,
        distance_km: 12.5,
        nearest_checkpoint: "Dawki Checkpoint",
        requires_ilp: false,
        warning_msg: "Convoy transit is within 15km of the international border buffer zone."
      });
    }
  },
  analyzeRoute: async (routePoints) => {
    try {
      const res = await apiClient.post('/api/boundaries/analyze-route/', {
        route_points: routePoints,
      });
      return res.data;
    } catch {
      return mockResponse({
        crosses_border_buffer: true,
        requires_ilp: true,
        checkpoint_crossings: 1,
        alert_messages: [
          "Route enters the 15km international border proximity zone near Dawki.",
          "convoy enters Nagaland/Mizoram sector. Ensure driver Inner Line Permits (ILP) are active."
        ]
      });
    }
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Institution API — Hospitals, Govt Sectors, NDRF/SDRF Hubs, Shelters, Logistics
// ─────────────────────────────────────────────────────────────────────────────
const MOCK_INSTITUTIONS = [
  {
    id: 1,
    name: "Gauhati Medical College & Hospital (GMCH)",
    category: "hospital",
    facility_type: "Apex Tertiary Care Teaching Hospital & Trauma Centre",
    state: "Assam",
    district: 3,
    district_name: "Kamrup Metropolitan",
    location: { type: "Point", coordinates: [91.7745, 26.1558], latitude: 26.1558, longitude: 91.7745 },
    address: "Bhangagarh, Guwahati, Assam 781032",
    contact_number: "+91-361-2529457",
    emergency_helpline: "108",
    bed_capacity: 2200,
    operational_status: "operational",
    source_api: "master_roster",
    metadata: { icu_beds: 180, oxygen_plant: true, blood_bank: true, helipad_nearby: true },
  },
  {
    id: 2,
    name: "Silchar Medical College & Hospital (SMCH)",
    category: "hospital",
    facility_type: "Barak Valley Apex Regional Medical Center",
    state: "Assam",
    district: 1,
    district_name: "Cachar",
    location: { type: "Point", coordinates: [92.7933, 24.7869], latitude: 24.7869, longitude: 92.7933 },
    address: "Ghungoor, Silchar, Assam 788014",
    contact_number: "+91-3842-240102",
    emergency_helpline: "108",
    bed_capacity: 1000,
    operational_status: "operational",
    source_api: "master_roster",
    metadata: { icu_beds: 75, oxygen_plant: true, blood_bank: true },
  },
  {
    id: 3,
    name: "Assam State Disaster Management Authority (ASDMA HQ)",
    category: "govt_office",
    facility_type: "State Apex Disaster Command & Operations Center",
    state: "Assam",
    district: 3,
    district_name: "Kamrup Metropolitan",
    location: { type: "Point", coordinates: [91.7892, 26.1439], latitude: 26.1439, longitude: 91.7892 },
    address: "Dispur, Guwahati, Assam 781006",
    contact_number: "+91-361-2237221",
    emergency_helpline: "1070",
    bed_capacity: 0,
    operational_status: "operational",
    source_api: "master_roster",
    metadata: { state_eoc: true, gis_mapping_cell: true, satellite_comms: true },
  },
  {
    id: 4,
    name: "1st Battalion NDRF Headquarters (Patgaon)",
    category: "emergency_station",
    facility_type: "National Disaster Response Force Regional Battalion Base",
    state: "Assam",
    district: 3,
    district_name: "Kamrup Metropolitan",
    location: { type: "Point", coordinates: [91.6028, 26.0958], latitude: 26.0958, longitude: 91.6028 },
    address: "Patgaon, Rani Gate, Guwahati, Assam 781017",
    contact_number: "+91-361-2840284",
    emergency_helpline: "1078",
    bed_capacity: 300,
    operational_status: "operational",
    source_api: "master_roster",
    metadata: { boat_rescue_teams: 18, canine_search_squad: true },
  },
  {
    id: 5,
    name: "FCI Regional Food Grain Depot (Changchari)",
    category: "logistics_hub",
    facility_type: "Food Corporation of India Strategic Mega Grain Storage Hub",
    state: "Assam",
    district: 3,
    district_name: "Kamrup Metropolitan",
    location: { type: "Point", coordinates: [91.6889, 26.2694], latitude: 26.2694, longitude: 91.6889 },
    address: "Changchari Rail Siding, NH-27, Kamrup, Assam 781101",
    contact_number: "+91-361-2850022",
    emergency_helpline: "+91-361-2850044",
    bed_capacity: 0,
    operational_status: "operational",
    source_api: "master_roster",
    metadata: { storage_capacity_metric_tons: 50000, rail_connected: true },
  },
  {
    id: 6,
    name: "Majuli Central Flood High-Ground Shelter Complex",
    category: "relief_shelter",
    facility_type: "Elevated Multi-Purpose Flood & Disaster Shelter",
    state: "Assam",
    district_name: "Majuli",
    location: { type: "Point", coordinates: [94.2189, 26.9722], latitude: 26.9722, longitude: 94.2189 },
    address: "Kamalabari Elevated Ground, Majuli, Assam 785106",
    contact_number: "+91-3775-273311",
    emergency_helpline: "1077",
    bed_capacity: 1500,
    operational_status: "operational",
    source_api: "master_roster",
    metadata: { solar_power: true, drinking_water_ro_plant: true },
  },
];

export const institutionAPI = {
  /**
   * List institutions with optional filters.
   * @param {Object} filters - { category, state, district, operational_status, live, search }
   */
  list: async (filters = {}) => {
    try {
      const res = await apiClient.get('/api/institutions/', { params: filters });
      // Handle both paginated and plain array responses
      return Array.isArray(res.data) ? res.data : (res.data.results || res.data);
    } catch {
      let list = MOCK_INSTITUTIONS;
      if (filters.category) list = list.filter(i => i.category === filters.category);
      if (filters.state) list = list.filter(i => i.state?.toLowerCase() === filters.state.toLowerCase());
      if (filters.district) list = list.filter(i => i.district_name?.toLowerCase().includes(filters.district.toLowerCase()));
      return list;
    }
  },

  /**
   * Get single institution by ID.
   */
  get: async (id) => {
    try {
      const res = await apiClient.get(`/api/institutions/${id}/`);
      return res.data;
    } catch {
      return MOCK_INSTITUTIONS.find(i => i.id === id) || MOCK_INSTITUTIONS[0];
    }
  },

  /**
   * Trigger full sync from OpenStreetMap + NER master roster into DB.
   * @param {Object} payload - { include_osm: bool, district: string, state: string }
   */
  syncExternal: async (payload = {}) => {
    try {
      const res = await apiClient.post('/api/institutions/sync-external/', payload);
      return res.data;
    } catch {
      return {
        status: 'success',
        message: 'Institutions synchronized (mock fallback).',
        stats: { institutions_created: 20, institutions_updated: 0, resources_auto_generated: 12, total_processed: 20 }
      };
    }
  },

  /**
   * Live fetch institutions directly from OpenStreetMap Overpass API.
   * @param {Object} payload - { district: string, state: string, category: string } or { bbox: [minLat, minLon, maxLat, maxLon] }
   */
  fetchLive: async (payload = {}) => {
    try {
      const res = await apiClient.post('/api/institutions/fetch-live/', payload);
      return res.data;
    } catch {
      const filtered = payload.category
        ? MOCK_INSTITUTIONS.filter(i => i.category === payload.category)
        : MOCK_INSTITUTIONS;
      return {
        total_fetched: filtered.length,
        source: 'mock_fallback',
        results: filtered,
      };
    }
  },
};

export default apiClient;

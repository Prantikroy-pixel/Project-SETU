import React from 'react';
import { Polyline, Popup } from 'react-leaflet';
import { Navigation } from 'lucide-react';

/**
 * 3-Tier Risk Division Definitions:
 * 1. Red (Nearly Red / Crimson #DC2626): Risk >= 0.70 (Near Blockage / Imminent / Critical)
 * 2. Yellow (Amber / Gold #F59E0B): 0.35 <= Risk < 0.70 (Very High Disruption Probability / Caution)
 * 3. Green (Emerald #10B981): Risk < 0.35 (Little to No Risk / Safe Transit)
 */
export const RISK_TIERS = {
  CRITICAL: {
    key: 'critical',
    label: 'Nearly Blocked / Critical Risk',
    shortLabel: 'Near-Blockage',
    color: '#DC2626',
    glowColor: 'rgba(220, 38, 38, 0.4)',
    badgeBg: 'bg-red-100 text-red-800 border-red-300',
    dotBg: 'bg-red-600',
    strokeWidth: 6,
    opacity: 0.95,
    dashArray: undefined,
    description: 'Imminent blockage / high disruption likelihood (< 3 hrs). Transit halted or severely obstructed.',
  },
  WARNING: {
    key: 'warning',
    label: 'High Probability Warning',
    shortLabel: 'High Risk',
    color: '#F59E0B',
    glowColor: 'rgba(245, 158, 11, 0.4)',
    badgeBg: 'bg-amber-100 text-amber-900 border-amber-300',
    dotBg: 'bg-amber-500',
    strokeWidth: 5,
    opacity: 0.9,
    dashArray: '8, 6',
    description: 'Elevated hazard probability. Heavy rainfall or steep slope alert. High risk of delay.',
  },
  SAFE: {
    key: 'safe',
    label: 'Safe / Clear Corridor',
    shortLabel: 'Safe Route',
    color: '#10B981',
    glowColor: 'rgba(16, 185, 129, 0.3)',
    badgeBg: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    dotBg: 'bg-emerald-600',
    strokeWidth: 4,
    opacity: 0.85,
    dashArray: undefined,
    description: 'Optimal road conditions. Little to no risk detected. Clear transit recommended.',
  },
};

/**
 * Classify any risk value (0.0 to 1.0 or 0 to 100) or status into the 3 Divisions
 */
export function getRiskDivision(score, conditionType = '', status = '') {
  const normScore = typeof score === 'number' ? (score > 1 ? score / 100 : score) : 0;
  const statusLower = String(status || '').toLowerCase();
  const typeLower = String(conditionType || '').toLowerCase();

  const isBlocked = ['blocked', 'flooded', 'landslide', 'closed', 'impassable', 'critical', 'severe_bottleneck'].some(
    (kw) => statusLower.includes(kw) || typeLower.includes(kw)
  );

  if (isBlocked || normScore >= 0.70) {
    return {
      ...RISK_TIERS.CRITICAL,
      score: Math.max(normScore, isBlocked ? 0.88 : normScore),
      percentage: Math.round(Math.max(normScore, isBlocked ? 0.88 : normScore) * 100),
    };
  }

  if (statusLower.includes('moderate_stress') || statusLower.includes('warning') || normScore >= 0.35) {
    return {
      ...RISK_TIERS.WARNING,
      score: normScore,
      percentage: Math.round(normScore * 100),
    };
  }

  return {
    ...RISK_TIERS.SAFE,
    score: normScore,
    percentage: Math.round(normScore * 100),
  };
}

/**
 * Key Arterial Highway Lifeline Corridors Across Northeast India (NER)
 */
export const NER_HIGHWAY_CORRIDORS = [
  {
    id: 'corridor-nh6-shillong-silchar',
    name: 'NH-6 Meghalaya – Barak Lifeline',
    section: 'Shillong – Jowai – Haflong Pass – Silchar',
    baseRisk: 0.82, // Landslide prone mountain corridor
    hazardDetails: 'Severe slope grade (26°), heavy monsoon runoff, saturated hill cut soil.',
    lengthKm: 215,
    path: [
      [25.5788, 91.8933], // Shillong
      [25.4500, 92.2000], // Jowai
      [25.3200, 92.4800], // Khliehriat
      [25.1812, 93.0175], // Haflong / Lumshnong Ridge
      [24.9600, 92.8900], // Kalain
      [24.8333, 92.7789], // Silchar
    ],
  },
  {
    id: 'corridor-nh306-silchar-aizawl',
    name: 'NH-306 Silchar – Mizoram Lifeline',
    section: 'Silchar – Vairengte – Kolasib – Aizawl',
    baseRisk: 0.75, // Critical hillside cut
    hazardDetails: 'High mudflow probability, active road breach reports near Vairengte.',
    lengthKm: 140,
    path: [
      [24.8333, 92.7789], // Silchar
      [24.6200, 92.7400], // Dholai
      [24.5050, 92.7600], // Vairengte Checkpost
      [24.2250, 92.6780], // Kolasib
      [23.9500, 92.7100], // Sairang
      [23.7271, 92.7176], // Aizawl
    ],
  },
  {
    id: 'corridor-nh27-guwahati-nagaon-jorhat',
    name: 'NH-27 Upper Assam Arterial',
    section: 'Guwahati – Nagaon – Kaziranga – Jorhat – Dibrugarh',
    baseRisk: 0.22, // Mostly clear 4-lane plain
    hazardDetails: 'Optimal drainage, low grade, minor flood buffer alert near Kaziranga bypass.',
    lengthKm: 440,
    path: [
      [26.1445, 91.7362], // Guwahati
      [26.2000, 92.1500], // Jagiroad
      [26.3450, 92.6840], // Nagaon
      [26.5800, 93.1700], // Kaziranga
      [26.6500, 93.9700], // Bokakhat
      [26.8000, 94.2600], // Jorhat
      [27.4728, 94.9120], // Dibrugarh
    ],
  },
  {
    id: 'corridor-nh8-silchar-agartala',
    name: 'NH-8 Tripura National Highway',
    section: 'Silchar – Karimganj – Churaibari – Dharmanagar – Agartala',
    baseRisk: 0.48, // Moderate-High rain hazard
    hazardDetails: 'Moderate rain accumulation (45mm/24h), cautionary bottleneck at Churaibari border.',
    lengthKm: 270,
    path: [
      [24.8333, 92.7789], // Silchar
      [24.8650, 92.3580], // Karimganj
      [24.6400, 92.2400], // Churaibari
      [24.3800, 92.1600], // Dharmanagar
      [24.1600, 91.7800], // Teliamura
      [23.8315, 91.2868], // Agartala
    ],
  },
  {
    id: 'corridor-nh29-dimapur-kohima',
    name: 'NH-29 Nagaland Mountain Pass',
    section: 'Dimapur – Chumukedima – Phesama – Kohima',
    baseRisk: 0.78, // High landslide vulnerability
    hazardDetails: 'Active rockfall hazard, steep mountain inclines (30°), rain-triggered fissures.',
    lengthKm: 74,
    path: [
      [25.9090, 93.7266], // Dimapur
      [25.8200, 93.7900], // Chumukedima
      [25.7500, 93.9200], // Medziphema
      [25.6751, 94.1086], // Kohima
    ],
  },
  {
    id: 'corridor-nh37-jiribam-imphal',
    name: 'NH-37 Manipur Mountain Lifeline',
    section: 'Silchar – Jiribam – Noney – Imphal',
    baseRisk: 0.68, // Elevated hazard
    hazardDetails: 'River bridge crossing bottleneck, moderate rockslide risk in Noney hills.',
    lengthKm: 220,
    path: [
      [24.8333, 92.7789], // Silchar
      [24.8000, 93.1200], // Jiribam
      [24.8100, 93.4500], // Nungba
      [24.7800, 93.7000], // Noney
      [24.8170, 93.9368], // Imphal
    ],
  },
  {
    id: 'corridor-nh415-itanagar-gateway',
    name: 'NH-415 Arunachal Pradesh Artery',
    section: 'Banderdewa – Naharlagun – Itanagar',
    baseRisk: 0.28, // Low to moderate
    hazardDetails: 'Stable road surface, clear mountain cut, minor culvert maintenance.',
    lengthKm: 42,
    path: [
      [27.1200, 93.8100], // Banderdewa
      [27.1000, 93.6900], // Nirjuli
      [27.0900, 93.6400], // Naharlagun
      [27.0844, 93.6053], // Itanagar
    ],
  },
  {
    id: 'corridor-nh10-siliguri-gangtok',
    name: 'NH-10 Teesta Landslide Highway',
    section: 'Siliguri – Sevoke – Teesta Bazaar – Rangpo – Gangtok',
    baseRisk: 0.85, // Critical landslide zone
    hazardDetails: 'Teesta river surge risk, high active rockfall zone at 29th Mile.',
    lengthKm: 114,
    path: [
      [26.7271, 88.3953], // Siliguri
      [26.8800, 88.4700], // Sevoke
      [27.0500, 88.4900], // Teesta Bazaar
      [27.1800, 88.5300], // Rangpo
      [27.3389, 88.6065], // Gangtok
    ],
  },
  {
    id: 'corridor-barak-internal-cachar',
    name: 'Barak Valley Arterial Link',
    section: 'Silchar – Udharbond – Kumbhirgram Airport – Badarpur',
    baseRisk: 0.32,
    hazardDetails: 'Minor waterlogging in low-lying tea estate sections, overall clear passage.',
    lengthKm: 55,
    path: [
      [24.8333, 92.7789], // Silchar
      [24.8900, 92.8900], // Udharbond
      [24.9100, 92.9800], // Kumbhirgram
      [24.8700, 92.5800], // Badarpur
    ],
  },
  {
    id: 'corridor-brahmaputra-flood-corridor',
    name: 'Brahmaputra Flood Plain Route',
    section: 'Guwahati – Hajo – Barpeta – Bongaigaon',
    baseRisk: 0.55,
    hazardDetails: 'Elevated river flood basin risk, heavy 24h catchment rainfall alert.',
    lengthKm: 175,
    path: [
      [26.1445, 91.7362], // Guwahati
      [26.2500, 91.5300], // Hajo
      [26.3079, 90.9971], // Barpeta
      [26.4603, 90.6464], // Bongaigaon
    ],
  },
];

/**
 * Floating 3-Tier Risk Path Legend Control
 */
export function RiskLegendControl({ className = '', compact = false }) {
  return (
    <div
      className={`bg-white/95 backdrop-blur-md p-3 rounded-xl border border-slate-200/90 shadow-lg text-xs z-[1000] pointer-events-auto transition-all select-none ${className}`}
      style={{ minWidth: compact ? '200px' : '260px' }}
    >
      <div className="flex items-center justify-between border-b border-slate-100 pb-1.5 mb-2">
        <span className="font-extrabold text-[11px] uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
          <Navigation className="w-3.5 h-3.5 text-primary-600" />
          <span>Corridor Risk Divisions</span>
        </span>
        <span className="text-[9px] font-bold text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">3-TIER PATH</span>
      </div>

      <div className="space-y-1.5">
        {/* Tier 1: Red */}
        <div className="flex items-center justify-between p-1.5 rounded-lg bg-red-50/70 border border-red-200/80">
          <div className="flex items-center gap-2">
            <div className="w-4 h-1.5 rounded-full bg-red-600 shadow-sm animate-pulse"></div>
            <div>
              <div className="text-[11px] font-extrabold text-red-900 leading-tight">Nearly Blocked / Critical</div>
              {!compact && <div className="text-[9px] text-red-700 font-medium">Imminent blockage (Risk ≥ 70%)</div>}
            </div>
          </div>
          <span className="text-[10px] font-black px-1.5 py-0.5 rounded bg-red-600 text-white shadow-xs">
            ≥ 70%
          </span>
        </div>

        {/* Tier 2: Yellow */}
        <div className="flex items-center justify-between p-1.5 rounded-lg bg-amber-50/70 border border-amber-200/80">
          <div className="flex items-center gap-2">
            <div className="w-4 h-1.5 rounded-full bg-amber-500 shadow-sm"></div>
            <div>
              <div className="text-[11px] font-extrabold text-amber-900 leading-tight">High Probability Warning</div>
              {!compact && <div className="text-[9px] text-amber-700 font-medium">High disruption risk (35% – 69%)</div>}
            </div>
          </div>
          <span className="text-[10px] font-black px-1.5 py-0.5 rounded bg-amber-500 text-white shadow-xs">
            35–69%
          </span>
        </div>

        {/* Tier 3: Green */}
        <div className="flex items-center justify-between p-1.5 rounded-lg bg-emerald-50/70 border border-emerald-200/80">
          <div className="flex items-center gap-2">
            <div className="w-4 h-1.5 rounded-full bg-emerald-600 shadow-sm"></div>
            <div>
              <div className="text-[11px] font-extrabold text-emerald-900 leading-tight">Safe / Clear Corridor</div>
              {!compact && <div className="text-[9px] text-emerald-700 font-medium">Optimal transit (Risk &lt; 35%)</div>}
            </div>
          </div>
          <span className="text-[10px] font-black px-1.5 py-0.5 rounded bg-emerald-600 text-white shadow-xs">
            &lt; 35%
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * Renders all Highway Corridors across the Map with dynamic 3-tier risk coloring and popups
 */
export function RiskCorridorMapLayer({
  conditions = [],
  highlightCorridorId = null,
  onCorridorSelect = null,
}) {
  // Compute real-time risk for each corridor based on active conditions and base factors
  const corridorsWithLiveRisk = NER_HIGHWAY_CORRIDORS.map((corridor) => {
    let effectiveRisk = corridor.baseRisk;

    // Check if any active condition matches or is near this corridor
    const matchingHazards = (conditions || []).filter((c) => {
      const val = String(c.value || '').toLowerCase();
      const isRoadBlock = c.condition_type === 'road_status' && ['blocked', 'landslide', 'flooded', 'closed'].includes(val);
      if (isRoadBlock && c.district_name) {
        return corridor.section.toLowerCase().includes(c.district_name.toLowerCase());
      }
      return false;
    });

    if (matchingHazards.length > 0) {
      effectiveRisk = Math.max(effectiveRisk, 0.88);
    }

    const division = getRiskDivision(effectiveRisk);

    return {
      ...corridor,
      effectiveRisk,
      division,
      activeHazardsCount: matchingHazards.length,
    };
  });

  return (
    <>
      {corridorsWithLiveRisk.map((corridor) => {
        const isHighlighted = highlightCorridorId === corridor.id;
        const { division } = corridor;

        return (
          <React.Fragment key={corridor.id}>
            {/* Background halo for high visibility and contrast */}
            <Polyline
              positions={corridor.path}
              pathOptions={{
                color: '#ffffff',
                weight: (division.strokeWidth || 5) + 3,
                opacity: 0.8,
                lineCap: 'round',
                lineJoin: 'round',
              }}
            />

            {/* Main Risk-Colored Path */}
            <Polyline
              positions={corridor.path}
              pathOptions={{
                color: division.color,
                weight: isHighlighted ? (division.strokeWidth || 5) + 2 : division.strokeWidth || 5,
                opacity: division.opacity || 0.9,
                dashArray: division.dashArray,
                lineCap: 'round',
                lineJoin: 'round',
              }}
              eventHandlers={{
                click: () => {
                  if (onCorridorSelect) onCorridorSelect(corridor);
                },
              }}
            >
              <Popup>
                <div className="text-xs p-1 space-y-2" style={{ minWidth: '220px' }}>
                  <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-1.5">
                    <div>
                      <div className="font-extrabold text-slate-900 text-sm">{corridor.name}</div>
                      <div className="text-[10px] text-slate-500 font-medium">{corridor.section}</div>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider border shrink-0 ${division.badgeBg}`}
                    >
                      {division.percentage}% RISK
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <span
                      className={`w-2.5 h-2.5 rounded-full shrink-0 ${division.dotBg} ${
                        division.key === 'critical' ? 'animate-pulse' : ''
                      }`}
                    ></span>
                    <span className="font-extrabold text-slate-800">{division.label}</span>
                  </div>

                  <div className="bg-slate-50 p-2 rounded border border-slate-200 text-[11px] text-slate-700 leading-relaxed font-medium">
                    {corridor.hazardDetails}
                  </div>

                  <div className="flex justify-between items-center text-[10px] text-slate-500 pt-1 border-t border-slate-100 font-semibold">
                    <span>Corridor Length: {corridor.lengthKm} km</span>
                    <span className="font-bold text-slate-700">
                      {division.key === 'critical'
                        ? '⚠️ Bypass Advised'
                        : division.key === 'warning'
                        ? '⚡ Proceed with Caution'
                        : '✅ Clear Transit'}
                    </span>
                  </div>
                </div>
              </Popup>
            </Polyline>
          </React.Fragment>
        );
      })}
    </>
  );
}

/**
 * Renders any dynamic single route (e.g. from vehicle allocation or border audit)
 * colored according to the 3-Tier Risk System
 */
export function RiskSegmentedRoute({
  routeCoordinates = [],
  riskScore = 0.2,
  label = 'Transit Route',
  statusText = 'Active Dispatch',
  originName = 'Origin Depot',
  destName = 'Destination',
}) {
  if (!routeCoordinates || routeCoordinates.length < 2) return null;

  const division = getRiskDivision(riskScore);

  return (
    <>
      {/* Route Outline / Halo */}
      <Polyline
        positions={routeCoordinates}
        pathOptions={{
          color: '#ffffff',
          weight: 8,
          opacity: 0.85,
          lineCap: 'round',
          lineJoin: 'round',
        }}
      />

      {/* Main 3-Tier Color Route */}
      <Polyline
        positions={routeCoordinates}
        pathOptions={{
          color: division.color,
          weight: 6,
          opacity: 0.95,
          dashArray: division.dashArray,
          lineCap: 'round',
          lineJoin: 'round',
        }}
      >
        <Popup>
          <div className="text-xs p-1 space-y-2" style={{ minWidth: '220px' }}>
            <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-1.5">
              <div>
                <div className="font-extrabold text-slate-900 text-sm">{label}</div>
                <div className="text-[10px] text-slate-500 font-medium">{originName} → {destName}</div>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider border shrink-0 ${division.badgeBg}`}>
                {division.percentage}% RISK
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${division.dotBg} ${division.key === 'critical' ? 'animate-pulse' : ''}`}></span>
              <span className="font-extrabold text-slate-800">{division.label}</span>
            </div>

            <p className="text-[11px] text-slate-600 leading-relaxed font-medium">
              {division.description}
            </p>

            <div className="flex justify-between items-center text-[10px] text-slate-500 pt-1 border-t border-slate-100 font-semibold">
              <span>Status: {statusText}</span>
              <span className="font-bold text-slate-700">
                {division.key === 'critical' ? '⚠️ Near-Blockage Alert' : division.key === 'warning' ? '⚡ High Delay Risk' : '✅ Optimal Corridor'}
              </span>
            </div>
          </div>
        </Popup>
      </Polyline>
    </>
  );
}

export default RiskCorridorMapLayer;

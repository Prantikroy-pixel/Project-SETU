import React, { useState, useEffect } from 'react';
import { Activity, Radio, CloudRain, Wind, Compass, RefreshCw, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function RealtimeTelemetryBanner({
  conditions = [],
  districtName = 'Barak Valley / NER',
  onRefresh = null,
  isRefreshing = false,
}) {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [liveWeather, setLiveWeather] = useState({
    rainfallMm: 38.4,
    windKmh: 16.2,
    humidity: 91,
    status: 'Monsoon Runoff Watch',
  });

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const criticalCount = (conditions || []).filter((c) => {
    const s = c.risk_score || 0;
    const v = String(c.value || '').toLowerCase();
    return s >= 0.7 || ['blocked', 'landslide', 'closed', 'critical'].some((k) => v.includes(k));
  }).length;

  const highCount = (conditions || []).filter((c) => {
    const s = c.risk_score || 0;
    const v = String(c.value || '').toLowerCase();
    return (s >= 0.45 && s < 0.7) || ['flooded', 'inundated', 'high', 'warning'].some((k) => v.includes(k));
  }).length;

  return (
    <div className="bg-slate-900 text-white px-4 py-2.5 rounded-lg border border-slate-800 shadow-md flex flex-wrap items-center justify-between gap-3 text-xs mb-4">
      {/* Left: Pulse Indicator & Live Status */}
      <div className="flex items-center gap-2.5">
        <div className="relative flex items-center justify-center">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
          <span className="absolute w-4 h-4 rounded-full bg-emerald-400 opacity-75 animate-ping"></span>
        </div>
        <div>
          <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[11px] text-slate-200">
            <span>LIVE TELEMETRY FEED</span>
            <span className="text-[10px] text-emerald-400 font-mono">● ACTIVE</span>
          </div>
          <div className="text-[10px] text-slate-400 font-mono">
            {currentTime.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })} IST | Sector: {districtName}
          </div>
        </div>
      </div>

      {/* Middle: Active Impact Summary */}
      <div className="flex items-center gap-2">
        <div className={`px-2 py-1 rounded border flex items-center gap-1.5 ${
          criticalCount > 0 
            ? 'bg-red-950/80 border-red-700/80 text-red-300 font-extrabold animate-pulse' 
            : 'bg-slate-800 border-slate-700 text-slate-300'
        }`}>
          <span className="w-2 h-2 rounded-full bg-red-500"></span>
          <span>{criticalCount} Critical Blockages</span>
        </div>

        <div className={`px-2 py-1 rounded border flex items-center gap-1.5 ${
          highCount > 0 
            ? 'bg-amber-950/80 border-amber-700/80 text-amber-300 font-bold' 
            : 'bg-slate-800 border-slate-700 text-slate-300'
        }`}>
          <span className="w-2 h-2 rounded-full bg-amber-500"></span>
          <span>{highCount} Flooded Sectors</span>
        </div>
      </div>

      {/* Right: Live Environment Telemetry & Refresh */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-3 text-slate-300 text-[11px] font-mono border-l border-slate-700 pl-3">
          <div className="flex items-center gap-1">
            <CloudRain className="w-3.5 h-3.5 text-sky-400" />
            <span>{liveWeather.rainfallMm}mm/24h</span>
          </div>
          <div className="flex items-center gap-1">
            <Wind className="w-3.5 h-3.5 text-teal-400" />
            <span>{liveWeather.windKmh} km/h</span>
          </div>
        </div>

        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition-all cursor-pointer disabled:opacity-50"
            title="Poll Latest Ground Reports"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-primary-400' : ''}`} />
          </button>
        )}
      </div>
    </div>
  );
}

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { boundaryAPI } from '../api';
import {
  Truck,
  Play,
  Pause,
  RotateCcw,
  AlertTriangle,
  ShieldCheck,
  Navigation,
  Compass,
  Zap,
  Activity,
  CheckCircle2,
  AlertOctagon,
  ArrowRight,
  Radio,
  Gauge,
  Layers,
} from 'lucide-react';

const PRIMARY_CONVOY_PATH = [
  { lat: 26.1445, lon: 91.7362, name: 'Guwahati Strategic Logistics Hub' },
  { lat: 25.5788, lon: 91.8933, name: 'Shillong Bypass Pass' },
  { lat: 25.4500, lon: 92.2000, name: 'Jowai Checkpoint' },
  { lat: 25.1812, lon: 92.3800, name: 'Lumshnong Vulnerable Pass' },
  { lat: 24.8333, lon: 92.7789, name: 'Silchar Central Relief Depot' },
];

const ALTERNATIVE_SAFE_PATH = [
  { lat: 26.1445, lon: 91.7362, name: 'Guwahati Strategic Logistics Hub' },
  { lat: 26.3450, lon: 92.6840, name: 'Nagaon Junction' },
  { lat: 25.7500, lon: 93.1700, name: 'Lumding Safe Bypass Corridor' },
  { lat: 25.3200, lon: 93.1200, name: 'Maibang Safe Hill Cut' },
  { lat: 24.8333, lon: 92.7789, name: 'Silchar Central Relief Depot' },
];

export default function LiveGpsTrackerSimulation({ onUpdateSimulationState }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [isRerouted, setIsRerouted] = useState(false);
  const [injectedHazard, setInjectedHazard] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [speed, setSpeed] = useState(2500); // ms per waypoint

  const activePath = isRerouted ? ALTERNATIVE_SAFE_PATH : PRIMARY_CONVOY_PATH;
  const currentVehiclePos = activePath[Math.min(currentStep, activePath.length - 1)];

  // Sync simulation state up to parent Map layer
  const syncState = useCallback(() => {
    if (onUpdateSimulationState) {
      onUpdateSimulationState({
        vehiclePos: currentVehiclePos,
        currentPath: activePath,
        isRerouted,
        injectedHazard,
        scanMetrics: {
          riskScore: scanResult?.primary_route_scan?.route_composite_risk ?? (injectedHazard ? 0.84 : 0.22),
          threatLevel: scanResult?.primary_route_scan?.threat_level ?? (injectedHazard ? 'critical' : 'low'),
          statusLabel: scanResult?.primary_route_scan?.status_label ?? (injectedHazard ? 'Hazard Blockage Detected' : 'Corridor Clear'),
        },
      });
    }
  }, [currentVehiclePos, activePath, isRerouted, injectedHazard, scanResult, onUpdateSimulationState]);

  useEffect(() => {
    syncState();
  }, [syncState]);

  // Periodic GPS convoy motion simulation
  useEffect(() => {
    let timer;
    if (isPlaying) {
      timer = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= activePath.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, speed);
    }
    return () => clearInterval(timer);
  }, [isPlaying, activePath.length, speed]);

  // Run AI Route Hazard Scan API
  const handleScanRoute = async (hazard) => {
    setScanning(true);
    try {
      const res = await boundaryAPI.scanRoute(PRIMARY_CONVOY_PATH, hazard);
      setScanResult(res);
      return res;
    } catch (err) {
      console.error('Route scan failed', err);
    } finally {
      setScanning(false);
    }
  };

  // Inject or remove simulated hazard
  const handleToggleHazard = async () => {
    if (injectedHazard) {
      setInjectedHazard(null);
      await handleScanRoute(null);
    } else {
      const hazard = {
        lat: 25.1812,
        lon: 92.3800,
        type: 'landslide',
        title: 'Landslide Blockage at Lumshnong Pass',
      };
      setInjectedHazard(hazard);
      const res = await handleScanRoute(hazard);
      if (res?.has_hazard_blockage) {
        // Auto-switch to alternative bypass
        setIsRerouted(true);
        setCurrentStep(0);
      }
    }
  };

  const handleManualReroute = () => {
    setIsRerouted((prev) => !prev);
    setCurrentStep(0);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStep(0);
    setIsRerouted(false);
    setInjectedHazard(null);
    setScanResult(null);
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-600">
            <Truck className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-black text-slate-900 flex items-center gap-2">
              <span>Live GPS Convoy Telemetry & AI Rerouting Engine</span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-200">
                <Radio className="w-2.5 h-2.5 animate-pulse text-emerald-600" />
                Live GPS
              </span>
            </h3>
            <p className="text-[11px] text-slate-500 font-medium">
              Real-time vehicle simulation along strategic corridors with proactive AI hazard avoidance.
            </p>
          </div>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all shadow-sm ${
              isPlaying
                ? 'bg-amber-500 hover:bg-amber-600 text-white'
                : 'bg-primary hover:bg-primary/90 text-on-primary'
            }`}
          >
            {isPlaying ? (
              <>
                <Pause className="w-3.5 h-3.5" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5" />
                <span>Simulate GPS</span>
              </>
            )}
          </button>

          <button
            onClick={handleReset}
            className="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg text-xs transition-colors"
            title="Reset Simulation"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Convoy Telemetry Status Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/70">
          <div className="text-[10px] uppercase font-bold text-slate-400">Target Vehicle</div>
          <div className="text-xs font-black text-slate-900 mt-0.5 flex items-center gap-1">
            <span>AS-11-BC-4401</span>
            <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-blue-100 text-blue-800">5-Ton</span>
          </div>
          <div className="text-[10px] text-slate-500 font-medium truncate mt-0.5">{currentVehiclePos.name}</div>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/70">
          <div className="text-[10px] uppercase font-bold text-slate-400">Active Corridor</div>
          <div className={`text-xs font-black mt-0.5 flex items-center gap-1 ${isRerouted ? 'text-emerald-700' : 'text-blue-700'}`}>
            <span>{isRerouted ? 'NH-27 Lumding Bypass' : 'NH-6 Meghalaya Pass'}</span>
          </div>
          <div className="text-[10px] text-slate-500 font-medium mt-0.5">
            {isRerouted ? 'Safe Autonomous Reroute' : 'Standard Primary Lifeline'}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/70">
          <div className="text-[10px] uppercase font-bold text-slate-400">AI Threat Level</div>
          <div className="text-xs font-black mt-0.5 flex items-center gap-1">
            {injectedHazard ? (
              <span className="text-red-600 flex items-center gap-1">
                <AlertOctagon className="w-3 h-3 text-red-500" />
                Critical Threat (0.84)
              </span>
            ) : (
              <span className="text-emerald-600 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-emerald-500" />
                Clear & Safe (0.22)
              </span>
            )}
          </div>
          <div className="text-[10px] text-slate-500 font-medium mt-0.5">
            {injectedHazard ? 'Disruption imminent on pass' : 'No blockages detected'}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/70">
          <div className="text-[10px] uppercase font-bold text-slate-400">Convoy Waypoint</div>
          <div className="text-xs font-black text-slate-900 mt-0.5">
            Step {currentStep + 1} of {activePath.length}
          </div>
          <div className="text-[10px] text-slate-500 font-medium mt-0.5 font-mono">
            {currentVehiclePos.lat.toFixed(4)}°N, {currentVehiclePos.lon.toFixed(4)}°E
          </div>
        </div>
      </div>

      {/* Interactive Scenario Injector Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-3 bg-gradient-to-r from-slate-50 to-blue-50/40 rounded-lg border border-slate-200/80">
        <div className="flex items-center space-x-2">
          <button
            onClick={handleToggleHazard}
            disabled={scanning}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all shadow-xs ${
              injectedHazard
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-white border border-red-200 text-red-700 hover:bg-red-50'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>{injectedHazard ? 'Clear Injected Hazard' : 'Inject Landslide Blockage on NH-6'}</span>
          </button>

          <button
            onClick={handleManualReroute}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all shadow-xs ${
              isRerouted
                ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50'
            }`}
          >
            <Navigation className="w-3.5 h-3.5" />
            <span>{isRerouted ? 'Switch to NH-6 Lifeline' : 'Switch to NH-27 Bypass'}</span>
          </button>
        </div>

        {injectedHazard && (
          <div className="text-xs font-semibold text-red-700 flex items-center gap-1.5 animate-in fade-in">
            <span className="w-2 h-2 rounded-full bg-red-600 animate-ping"></span>
            <span>AI Automated Rerouting Activated: Diverting convoy via NH-27 Lumding Corridor (Saved ~180 mins).</span>
          </div>
        )}
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { Filter, Play, Pause, AlertOctagon } from 'lucide-react';
import { getAnomalies, getEvents } from '../services/api';

import { useNavigate } from 'react-router-dom';

const LiveStream = () => {
  const [isPaused, setIsPaused] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  const navigate = useNavigate();

  const isTest = localStorage.getItem('sentinel_username') === 'testuser';

  useEffect(() => {
    const load = async () => {
      try {
        // For demouser, we fetch BOTH anomalies and real events to show a complete stream
        const [anomRes, eventRes] = await Promise.all([getAnomalies(), getEvents(100)]);
        
        let allEvents = [];
        
        if (Array.isArray(eventRes?.data)) {
          allEvents = eventRes.data.map((e: any) => ({
            id: e.id || Math.random(),
            created_at: e.timestamp,
            threat_type: e.event_type || 'LOG_EVENT',
            severity_label: e.severity_label || 'INFO',
            source_ip: e.source_ip || '—',
            device_id: e.hostname || '—',
            narrative: e.raw_message || '—'
          }));
        }

        // Overlay anomalies if they exist
        if (Array.isArray(anomRes?.data)) {
          const anoms = anomRes.data.map((a: any) => ({
            ...a,
            severity_label: a.severity_label || 'HIGH',
            threat_type: a.threat_type || 'ANOMALY'
          }));
          allEvents = [...anoms, ...allEvents].slice(0, 100);
        }

        setEvents(allEvents);
      } catch (err) { console.error("Failed to fetch live stream", err); }
    };

    load();
    if (!isPaused) {
      const interval = setInterval(load, 2000);
      return () => clearInterval(interval);
    }
  }, [isPaused]);

  return (
    <div className="flex flex-col h-full space-y-4">
      <header className="flex justify-between items-center border-b border-[rgba(0,240,255,0.3)] pb-4">
        <div>
          <h2 className="text-3xl font-display font-bold text-white tracking-widest uppercase">Live Event Stream</h2>
          <p className="text-[var(--color-muted)] font-mono text-sm mt-1">Real-time log ingestion and anomaly detection feed.</p>
        </div>
        <div className="flex space-x-3 items-center">
          <div className="flex space-x-2 mr-4">
            <span className="hud-chip-critical text-xs cursor-pointer opacity-50 hover:opacity-100 transition-opacity">CRITICAL</span>
            <span className="hud-chip-warning text-xs cursor-pointer opacity-50 hover:opacity-100 transition-opacity">HIGH</span>
            <span className="border border-[var(--color-primary)] text-[var(--color-primary)] px-2 font-display text-xs font-bold cursor-pointer opacity-50 hover:opacity-100 transition-opacity">MEDIUM</span>
          </div>
          <button 
            onClick={() => setIsPaused(!isPaused)}
            className="hud-button flex items-center bg-transparent border border-[var(--color-primary)] text-[var(--color-primary)] hover:bg-[rgba(0,240,255,0.1)]"
          >
            {isPaused ? <Play size={16} className="mr-2"/> : <Pause size={16} className="mr-2"/>}
            {isPaused ? 'RESUME STREAM' : 'PAUSE STREAM'}
          </button>
        </div>
      </header>

      <div className="hud-panel flex-1 overflow-hidden flex flex-col border-[var(--color-primary)] shadow-[0_0_15px_rgba(0,240,255,0.05)]">
        <div className="flex bg-[rgba(0,0,0,0.5)] border-b border-[rgba(0,240,255,0.15)] p-3 text-xs font-display tracking-widest text-[var(--color-muted)] sticky top-0">
          <div className="w-24">TIMESTAMP</div>
          <div className="w-32">SOURCE</div>
          <div className="w-24">SEVERITY</div>
          <div className="w-36">SRC IP</div>
          <div className="w-36">DEST IP</div>
          <div className="flex-1">PAYLOAD</div>
          <div className="w-24 text-right">ACTION</div>
        </div>
        
        <div className="flex-1 overflow-y-auto bg-[#03060a]">
          {events.map((evt) => (
            <div key={evt.id} className="flex p-3 border-b border-[rgba(255,255,255,0.05)] hover:bg-[rgba(0,240,255,0.05)] text-sm font-mono transition-colors group">
              <div className="w-24 text-gray-400">
                {evt.created_at ? (evt.created_at.includes('T') ? evt.created_at.split('T')[1] : evt.created_at.split(' ')[1])?.split('.')[0] : 'NOW'}
              </div>
              <div className="w-32 text-[var(--color-primary)] truncate pr-2">{evt.threat_type || 'ANOMALY'}</div>
              <div className="w-24">
                <span className={
                  evt.severity_label === 'CRITICAL' ? 'text-[var(--color-critical)] font-bold' : 
                  evt.severity_label === 'HIGH' ? 'text-[var(--color-warning)] font-bold' : 
                  'text-[var(--color-primary)]'
                }>[{evt.severity_label || 'INFO'}]</span>
              </div>
              <div 
                className="w-36 text-white hover:text-[var(--color-primary)] cursor-pointer underline decoration-dotted underline-offset-4"
                onClick={() => navigate(`/app/intel?ip=${evt.source_ip}`)}
              >
                {evt.source_ip || 'LOCAL'}
              </div>
              <div className="w-36 text-gray-300">{evt.device_id?.substring(0, 8)}</div>
              <div className="flex-1 text-gray-400 truncate pr-4">{evt.narrative || evt.attack_type}</div>
              <div className="w-24 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                <button className="text-[var(--color-warning)] hover:text-white flex items-center justify-end w-full text-xs font-display uppercase tracking-wider">
                  <AlertOctagon size={12} className="mr-1"/> Flag FP
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LiveStream;

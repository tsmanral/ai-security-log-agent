import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { AlertTriangle, Clock, Database, Crosshair, Network, FileTerminal, ShieldOff } from 'lucide-react';

const IncidentDrilldown = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="flex flex-col h-full space-y-6 overflow-y-auto">
      <header className="flex justify-between items-start border-b border-[rgba(0,240,255,0.3)] pb-4">
        <div>
          <div className="flex items-center space-x-3 mb-2">
            <h2 className="text-3xl font-display font-bold text-white tracking-widest uppercase">{id || 'INC-4092'}</h2>
            <span className="hud-chip-critical text-xl px-3">CRITICAL</span>
            <span className="border border-[var(--color-primary)] text-[var(--color-primary)] font-display font-bold uppercase px-3 py-1 bg-[rgba(0,240,255,0.1)]">IN-PROGRESS</span>
          </div>
          <p className="text-[var(--color-muted)] font-mono text-sm">Unauthorized AD Admin Elevation detected via multiple anomalies.</p>
        </div>
        <div className="flex space-x-3">
          <Link to={`/incident/${id || 'INC-4092'}/playbook`} className="hud-button flex items-center">
            <FileTerminal size={16} className="mr-2" /> Launch Playbook
          </Link>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-6">
        {/* Left Col: Entity Details & Actions */}
        <div className="col-span-4 space-y-6">
          <div className="hud-panel p-5">
            <h3 className="font-display text-lg text-[var(--color-primary)] mb-4 border-b border-[rgba(0,240,255,0.15)] pb-2 flex items-center"><Crosshair className="mr-2" size={18}/> Entity Details</h3>
            
            <div className="space-y-4 font-mono text-sm">
              <div>
                <p className="text-[var(--color-muted)] text-xs mb-1">SOURCE IP</p>
                <p className="text-white">192.168.1.105 <span className="text-[var(--color-critical)] ml-2">(High Risk)</span></p>
              </div>
              <div>
                <p className="text-[var(--color-muted)] text-xs mb-1">DESTINATION</p>
                <p className="text-white">DC-01.corp.local (Active Directory)</p>
              </div>
              <div>
                <p className="text-[var(--color-muted)] text-xs mb-1">USER ACCOUNT</p>
                <p className="text-white">jdoe_admin</p>
              </div>
              <div>
                <p className="text-[var(--color-muted)] text-xs mb-1">MITRE TACTIC</p>
                <p className="text-[var(--color-warning)]">TA0004 (Privilege Escalation)</p>
              </div>
            </div>
          </div>

          <div className="hud-panel p-5 border-[var(--color-critical)]">
            <h3 className="font-display text-lg text-[var(--color-critical)] mb-4 border-b border-[rgba(255,42,109,0.15)] pb-2 flex items-center"><ShieldOff className="mr-2" size={18}/> Quick Actions</h3>
            <div className="space-y-3">
              <button className="w-full text-left px-4 py-2 bg-[rgba(255,42,109,0.1)] border border-[var(--color-critical)] text-white font-display uppercase tracking-widest hover:bg-[var(--color-critical)] hover:text-black transition-colors">
                Isolate Asset
              </button>
              <button className="w-full text-left px-4 py-2 bg-[rgba(255,214,0,0.1)] border border-[var(--color-warning)] text-white font-display uppercase tracking-widest hover:bg-[var(--color-warning)] hover:text-black transition-colors">
                Revoke Credentials
              </button>
              <button className="w-full text-left px-4 py-2 border border-[var(--color-primary)] text-[var(--color-primary)] font-display uppercase tracking-widest hover:bg-[rgba(0,240,255,0.1)] transition-colors">
                Escalate to Tier 3
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="hud-panel p-4 flex flex-col justify-center items-center relative overflow-hidden">
              <div className="absolute top-0 w-full h-1 bg-gradient-to-r from-transparent via-[var(--color-warning)] to-transparent opacity-50"></div>
              <span className="text-xs font-display text-[var(--color-muted)] tracking-widest text-center uppercase">Traffic Trend</span>
              <span className="text-xl font-display font-bold text-[var(--color-warning)] mt-1 drop-shadow-[0_0_8px_rgba(255,214,0,0.5)]">1.2 GB/s</span>
            </div>
            <div className="hud-panel p-4 flex flex-col justify-center items-center relative overflow-hidden">
              <div className="absolute top-0 w-full h-1 bg-gradient-to-r from-transparent via-[var(--color-critical)] to-transparent opacity-50"></div>
              <span className="text-xs font-display text-[var(--color-muted)] tracking-widest text-center uppercase">Attack Surface Reach</span>
              <span className="text-xl font-display font-bold text-[var(--color-critical)] mt-1 drop-shadow-[0_0_8px_rgba(255,42,109,0.5)]">94% PROBABILITY</span>
            </div>
          </div>
        </div>

        {/* Right Col: Timeline & Forensics */}
        <div className="col-span-8 space-y-6">
          <div className="hud-panel p-5">
            <h3 className="font-display text-lg text-[var(--color-primary)] mb-4 border-b border-[rgba(0,240,255,0.15)] pb-2 flex items-center"><Clock className="mr-2" size={18}/> Attack Timeline</h3>
            
            <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-[var(--color-primary)] before:to-transparent mt-6">
              
              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                <div className="flex items-center justify-center w-10 h-10 rounded-full border-2 border-[var(--color-primary)] bg-[var(--color-surface-dim)] group-[.is-active]:bg-[var(--color-primary)] text-[var(--color-surface-dim)] group-[.is-active]:text-black shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-[0_0_10px_var(--color-primary)] z-10">
                  <Database size={16} />
                </div>
                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 hud-panel border-[var(--color-critical)]">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-display font-bold text-[var(--color-critical)] uppercase tracking-wider">Privilege Escalation</span>
                    <span className="text-xs text-[var(--color-muted)] font-mono">10:04:12 UTC</span>
                  </div>
                  <p className="text-sm font-mono text-gray-300">User jdoe_admin added to Domain Admins group via script execution.</p>
                </div>
              </div>

              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                <div className="flex items-center justify-center w-10 h-10 rounded-full border-2 border-[var(--color-primary)] bg-[var(--color-surface-dim)] text-[var(--color-primary)] shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                  <Network size={16} />
                </div>
                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 hud-panel">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-display font-bold text-[var(--color-warning)] uppercase tracking-wider">Lateral Movement</span>
                    <span className="text-xs text-[var(--color-muted)] font-mono">10:02:45 UTC</span>
                  </div>
                  <p className="text-sm font-mono text-gray-300">RDP session established from 192.168.1.105 to DC-01.corp.local.</p>
                </div>
              </div>

              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                <div className="flex items-center justify-center w-10 h-10 rounded-full border-2 border-[var(--color-primary)] bg-[var(--color-surface-dim)] text-[var(--color-primary)] shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                  <AlertTriangle size={16} />
                </div>
                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 hud-panel">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-display font-bold text-[var(--color-primary)] uppercase tracking-wider">Initial Access</span>
                    <span className="text-xs text-[var(--color-muted)] font-mono">09:45:10 UTC</span>
                  </div>
                  <p className="text-sm font-mono text-gray-300">Anomalous login for user jdoe_admin outside normal working hours.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="hud-panel p-5">
            <h3 className="font-display text-lg text-[var(--color-primary)] mb-4 border-b border-[rgba(0,240,255,0.15)] pb-2 flex items-center"><FileTerminal className="mr-2" size={18}/> Forensics (Raw Log)</h3>
            <div className="bg-black border border-[rgba(255,255,255,0.1)] p-4 font-mono text-xs overflow-x-auto text-green-400">
              <pre>
{`[2026-04-17T10:04:12Z] EVENT_ID: 4728 (Security)
SOURCE: DC-01.corp.local
MESSAGE: A member was added to a security-enabled global group.
SUBJECT:
  Security ID: SYSTEM
  Account Name: DC-01$
  Account Domain: CORP
MEMBER:
  Security ID: CORP\\jdoe_admin
  Account Name: jdoe_admin
GROUP:
  Security ID: S-1-5-21-34234-34234-3423-512
  Group Name: Domain Admins
`}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IncidentDrilldown;

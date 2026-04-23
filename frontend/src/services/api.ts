import axios from 'axios';

// Create an Axios instance
const api = axios.create({
  baseURL: 'http://localhost:8000', // Update this based on where your FastAPI runs
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('sentinel_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ── Live simulation counters ──────────────────────────────────────────────────
let _liveEventCount = 1543290;
let _liveAnomCount  = 342;
let _lastTick       = Date.now();

const tickLive = () => {
  const elapsedSec = (Date.now() - _lastTick) / 1000;
  _lastTick = Date.now();
  _liveEventCount += Math.round(elapsedSec * (4200 + Math.random() * 100));
  if (Math.random() < 0.3) _liveAnomCount += Math.round(Math.random() * 3);
};

export const getLiveStats = () => ({ events: _liveEventCount, anomalies: _liveAnomCount });

const EVENT_TYPES = ['Failed Login','Port Scan','Lateral Movement','Data Exfil','Privilege Escalation','Malware C2','Brute Force','Policy Violation','DNS Tunneling','Ransomware Beacon','Outbound 443','SMB Traversal','SQL Injection','ARP Spoof','Token Hijack'];
const SEVERITIES  = ['CRITICAL','HIGH','HIGH','MEDIUM','MEDIUM','MEDIUM','LOW','LOW'];

export const generateEventStream = (count = 200, deviceFilter?: string[]): any[] => {
  if (!isTestUser()) return [];
  const rows: any[] = [];
  for (let i = 0; i < count; i++) {
    const sev = SEVERITIES[Math.floor(Math.random() * SEVERITIES.length)];
    const type = EVENT_TYPES[Math.floor(Math.random() * EVENT_TYPES.length)];
    const host = deviceFilter ? deviceFilter[Math.floor(Math.random() * deviceFilter.length)] : `SRV-${100 + Math.floor(Math.random() * 899)}`;
    
    rows.push({
      id: 1000000 + i,
      timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
      event_type: type,
      severity: sev,
      host: host,
      source_ip: `192.168.1.${10 + Math.floor(Math.random() * 200)}`,
      raw_message: `AI-Sentinel Alert: Detected potential ${type.toLowerCase()} activity on ${host}.`,
      status: 'OPEN'
    });
  }
  return rows.sort((a, b) => b.id - a.id);
};

export const getActiveDeviceFilter = (): string[] | undefined => {
  const user = localStorage.getItem('sentinel_username') || 'anon';
  const raw = localStorage.getItem(`sentinel_device_filter_${user}`);
  if (raw === null) return undefined;
  try {
    return JSON.parse(raw);
  } catch { return undefined; }
};

export const saveActiveDeviceFilter = (deviceIds: string[]) => {
  const user = localStorage.getItem('sentinel_username') || 'anon';
  localStorage.setItem(`sentinel_device_filter_${user}`, JSON.stringify(deviceIds));
  window.dispatchEvent(new Event('sentinel_state_change'));
};

// Rich mock entity data keyed by entity for testuser investigations
export const MOCK_ENTITIES: Record<string, any> = {
  'inc_101': {
    entity: 'inc_101', type: 'Incident', risk_score: 97,
    source_ip: '10.0.5.22', attack_type: 'Ransomware Activity', severity_label: 'CRITICAL',
    affected_hosts: ['WKS-112-X', 'FILE-SRV-01'],
    affected_users: ['CORP\\jsmith', 'CORP\\svc_admin_temp'],
    related_events: [
      { id: 1, timestamp: new Date(Date.now() - 5400000).toISOString(), type: 'Mass File Encryption Detected', source: 'EDR', severity: 'CRITICAL', detail: '4,231 files encrypted in 90s on WKS-112-X' },
      { id: 2, timestamp: new Date(Date.now() - 4800000).toISOString(), type: 'C2 Outbound Connection', source: 'Firewall', severity: 'CRITICAL', detail: 'Outbound to 185.15.202.13:443 - known C2 node' },
      { id: 3, timestamp: new Date(Date.now() - 3600000).toISOString(), type: 'Privilege Escalation via Token Impersonation', source: 'Windows Security', severity: 'HIGH', detail: 'CORP\\svc_admin_temp elevated to SYSTEM via SeImpersonatePrivilege' },
      { id: 4, timestamp: new Date(Date.now() - 1800000).toISOString(), type: 'Lateral Movement (SMB)', source: 'Network Flow', severity: 'HIGH', detail: 'SMB share enumeration from 10.0.5.22 to FILE-SRV-01' },
    ],
    relationships: [
      { type: 'Source IP', target: '10.0.5.22 (WKS-112-X)', iconType: 'network' },
      { type: 'Compromised User', target: 'CORP\\svc_admin_temp', iconType: 'user' },
      { type: 'C2 Server', target: '185.15.202.13 (Rostelecom, RU)', iconType: 'globe' },
      { type: 'Encrypted Path', target: '\\\\FILE-SRV-01\\shares\\finance\\*', iconType: 'file' },
    ],
    playbook: 'RANSOMWARE_RESPONSE',
  },
  'inc_102': {
    entity: 'inc_102', type: 'Incident', risk_score: 78,
    source_ip: '45.33.2.1', attack_type: 'Lateral Movement', severity_label: 'HIGH',
    affected_hosts: ['APP-SRV-02', 'DB-SRV-01'],
    affected_users: ['CORP\\jdoe'],
    related_events: [
      { id: 1, timestamp: new Date(Date.now() - 7200000).toISOString(), type: 'Pass-the-Hash Attack', source: 'Windows Security', severity: 'HIGH', detail: 'NTLM hash reuse from 45.33.2.1 to APP-SRV-02' },
      { id: 2, timestamp: new Date(Date.now() - 5400000).toISOString(), type: 'RDP Session from Unusual Host', source: 'Network Flow', severity: 'MEDIUM', detail: 'RDP to DB-SRV-01 from 45.33.2.1 outside business hours' },
      { id: 3, timestamp: new Date(Date.now() - 3600000).toISOString(), type: 'Database Dump via SQL Tools', source: 'DLP', severity: 'HIGH', detail: 'sqlcmd.exe exfiltrating 2.1GB from customer_db' },
    ],
    relationships: [
      { type: 'Source IP', target: '45.33.2.1 (APP-SRV-02)', iconType: 'network' },
      { type: 'Compromised User', target: 'CORP\\jdoe', iconType: 'user' },
      { type: 'Target DB', target: 'DB-SRV-01 (customer_db)', iconType: 'server' },
    ],
    playbook: 'AD_ELEVATION_RESPONSE',
  },
  'inc_103': {
    entity: 'inc_103', type: 'Incident', risk_score: 55,
    source_ip: '192.168.1.1', attack_type: 'Brute Force', severity_label: 'MEDIUM',
    affected_hosts: ['DC-01'],
    affected_users: ['admin', 'administrator', 'root'],
    related_events: [
      { id: 1, timestamp: new Date(Date.now() - 14400000).toISOString(), type: '847 Failed Login Attempts', source: 'Active Directory', severity: 'MEDIUM', detail: 'Credential stuffing from 192.168.1.1 on DC-01' },
      { id: 2, timestamp: new Date(Date.now() - 10800000).toISOString(), type: 'Account Lockout: admin', source: 'Active Directory', severity: 'HIGH', detail: 'Account admin locked after 5 failed attempts' },
    ],
    relationships: [{ type: 'Network', target: 'Internal Segment', iconType: 'network' }],
    playbook: null,
  },
  'inc_104': {
    entity: 'inc_104', type: 'Incident', risk_score: 94,
    source_ip: '10.0.5.22', attack_type: 'Privilege Escalation', severity_label: 'CRITICAL',
    affected_hosts: ['WKS-112-X'], affected_users: ['CORP\\jsmith'],
    related_events: [
      { id: 1, timestamp: new Date(Date.now() - 1800000).toISOString(), type: 'LSA Secrets Dump', source: 'EDR', severity: 'CRITICAL', detail: 'lsass.exe memory dumped to C:\\Windows\\Temp\\debug.bin' },
      { id: 2, timestamp: new Date(Date.now() - 900000).toISOString(), type: 'Scheduled Task Creation', source: 'Windows Security', severity: 'HIGH', detail: 'New task "Update" created to run as SYSTEM' },
    ],
    relationships: [{ type: 'Host', target: 'WKS-112-X', iconType: 'server' }],
    playbook: 'AD_ELEVATION_RESPONSE',
  },
  'inc_105': {
    entity: 'inc_105', type: 'Incident', risk_score: 88,
    source_ip: '45.33.2.1', attack_type: 'Data Exfiltration', severity_label: 'HIGH',
    affected_hosts: ['LNX-SRV-01'], affected_users: ['ubuntu'],
    related_events: [
      { id: 1, timestamp: new Date(Date.now() - 900000).toISOString(), type: 'Mass SCP Upload', source: 'Syslog', severity: 'HIGH', detail: '4.2GB uploaded to remote IP 8.8.8.8 via scp' },
    ],
    relationships: [{ type: 'Source', target: 'LNX-SRV-01', iconType: 'server' }],
    playbook: null,
  },
  '10.0.5.22': {
    entity: '10.0.5.22', type: 'IP', risk_score: 97,
    related_incidents: ['inc_101'],
    related_events: [
      { id: 1, timestamp: new Date(Date.now() - 5400000).toISOString(), type: 'Ransomware Activity', source: 'EDR', severity: 'CRITICAL', detail: 'WKS-112-X beacon — encryption payload deployed' },
      { id: 2, timestamp: new Date(Date.now() - 4800000).toISOString(), type: 'C2 Communication', source: 'Firewall', severity: 'CRITICAL', detail: 'Outbound to 185.15.202.13:443' },
    ],
    relationships: [
      { type: 'Hostname', target: 'WKS-112-X', iconType: 'server' },
      { type: 'Logged User', target: 'CORP\\jsmith', iconType: 'user' },
      { type: 'C2 Contact', target: '185.15.202.13 (RU)', iconType: 'globe' },
    ],
    playbook: 'RANSOMWARE_RESPONSE',
  },
  '45.33.2.1': {
    entity: '45.33.2.1', type: 'IP', risk_score: 78,
    related_incidents: ['inc_102'],
    related_events: [
      { id: 1, timestamp: new Date(Date.now() - 7200000).toISOString(), type: 'Pass-the-Hash', source: 'Windows Security', severity: 'HIGH', detail: 'NTLM credential reuse from APP-SRV-02' },
      { id: 2, timestamp: new Date(Date.now() - 5400000).toISOString(), type: 'Lateral RDP', source: 'Network Flow', severity: 'MEDIUM', detail: 'RDP to DB-SRV-01 outside business hours' },
    ],
    relationships: [
      { type: 'Hostname', target: 'APP-SRV-02', iconType: 'server' },
      { type: 'Logged User', target: 'CORP\\jdoe', iconType: 'user' },
      { type: 'Target', target: 'DB-SRV-01', iconType: 'server' },
    ],
    playbook: 'AD_ELEVATION_RESPONSE',
  },
  '192.168.1.1': {
    entity: '192.168.1.1', type: 'IP', risk_score: 55,
    source_ip: '192.168.1.1',
    attack_type: 'Brute Force',
    related_incidents: ['inc_103'],
    affected_hosts: ['DC-01'],
    affected_users: ['admin', 'administrator'],
    related_events: [
      { id: 1, timestamp: new Date(Date.now() - 14400000).toISOString(), type: '847 Failed Login Attempts', source: 'Active Directory', severity: 'MEDIUM', detail: 'Credential stuffing on DC-01 from 192.168.1.1 — Hydra pattern detected' },
      { id: 2, timestamp: new Date(Date.now() - 10800000).toISOString(), type: 'Account Lockout', source: 'Active Directory', severity: 'HIGH', detail: 'Account admin locked after threshold exceeded' },
    ],
    relationships: [
      { type: 'Target DC', target: 'DC-01 (Domain Controller)', iconType: 'server' },
      { type: 'Tool Pattern', target: 'Hydra / CrackMapExec', iconType: 'file' },
      { type: 'Related Incident', target: 'inc_103', iconType: 'network' },
    ],
    playbook: 'BRUTE_FORCE_RESPONSE',
  },
  'CORP\\jsmith': {
    entity: 'CORP\\jsmith', type: 'User', risk_score: 91,
    source_ip: '10.0.5.22',
    attack_type: 'Account Compromise',
    related_incidents: ['inc_101'],
    affected_hosts: ['WKS-112-X', 'FILE-SRV-01'],
    affected_users: ['CORP\\jsmith', 'CORP\\svc_admin_temp'],
    related_events: [
      { id: 1, timestamp: new Date(Date.now() - 6000000).toISOString(), type: 'Credentials Used in Ransomware', source: 'EDR', severity: 'CRITICAL', detail: 'jsmith credentials leveraged to deploy encryption payload on WKS-112-X' },
      { id: 2, timestamp: new Date(Date.now() - 5000000).toISOString(), type: 'Token Impersonation', source: 'Windows Security', severity: 'HIGH', detail: 'SeImpersonatePrivilege abused on CORP\\svc_admin_temp via jsmith session' },
    ],
    relationships: [
      { type: 'Primary Host', target: 'WKS-112-X', iconType: 'server' },
      { type: 'Source IP', target: '10.0.5.22', iconType: 'network' },
      { type: 'Impersonated', target: 'CORP\\svc_admin_temp', iconType: 'user' },
      { type: 'Related Incident', target: 'inc_101', iconType: 'network' },
    ],
    playbook: 'RANSOMWARE_RESPONSE',
  },
};

// Extended entity lookup — all pivot nodes clickable in the graph
const EXTRA_ENTITIES: Record<string, any> = {
  'WKS-112-X': { entity:'WKS-112-X', type:'Host', risk_score:95, source_ip:'10.0.5.22', attack_type:'Ransomware Victim', related_incidents:['inc_101'], affected_users:['CORP\\jsmith'], related_events:[{ id:1, timestamp:new Date(Date.now()-5400000).toISOString(), type:'Mass File Encryption', source:'EDR', severity:'CRITICAL', detail:'4,231 files encrypted in 90s on WKS-112-X' }, { id:2, timestamp:new Date(Date.now()-4900000).toISOString(), type:'Ransomware Note Dropped', source:'EDR', severity:'CRITICAL', detail:'README_HOW_TO_DECRYPT.txt created in 28 directories' }], relationships:[{ type:'User Session', target:'CORP\\jsmith', iconType:'user' }, { type:'Source IP', target:'10.0.5.22', iconType:'network' }, { type:'C2 Contact', target:'185.15.202.13', iconType:'globe' }], playbook:'RANSOMWARE_RESPONSE' },
  'FILE-SRV-01': { entity:'FILE-SRV-01', type:'Server', risk_score:82, source_ip:'10.0.0.10', attack_type:'Ransomware Target', related_incidents:['inc_101'], affected_users:['CORP\\jsmith'], related_events:[{ id:1, timestamp:new Date(Date.now()-5200000).toISOString(), type:'SMB Share Traversal', source:'Network Flow', severity:'HIGH', detail:'Lateral access to \\\\FILE-SRV-01\\shares\\finance\\*' }, { id:2, timestamp:new Date(Date.now()-5000000).toISOString(), type:'Mass File Modification', source:'EDR', severity:'CRITICAL', detail:'1,847 .xlsx files encrypted in finance share' }], relationships:[{ type:'Network Peer', target:'WKS-112-X', iconType:'server' }, { type:'Service Account', target:'CORP\\svc_admin_temp', iconType:'user' }], playbook:'RANSOMWARE_RESPONSE' },
  'DC-01': { entity:'DC-01', type:'Domain Controller', risk_score:60, source_ip:'172.16.0.1', attack_type:'Brute Force Target', related_incidents:['inc_103'], affected_users:['admin','administrator'], related_events:[{ id:1, timestamp:new Date(Date.now()-14400000).toISOString(), type:'847 Failed Logins', source:'Active Directory', severity:'MEDIUM', detail:'Credential stuffing from 192.168.1.1' }, { id:2, timestamp:new Date(Date.now()-10800000).toISOString(), type:'Account Lockout x3', source:'Active Directory', severity:'HIGH', detail:'admin/administrator/root locked out' }], relationships:[{ type:'Attacker IP', target:'192.168.1.1', iconType:'network' }, { type:'Domain', target:'CORP.LOCAL', iconType:'server' }], playbook:'BRUTE_FORCE_RESPONSE' },
  'APP-SRV-02': { entity:'APP-SRV-02', type:'Server', risk_score:75, source_ip:'45.33.2.1', attack_type:'Lateral Movement Target', related_incidents:['inc_102'], affected_users:['CORP\\jdoe'], related_events:[{ id:1, timestamp:new Date(Date.now()-7200000).toISOString(), type:'Pass-the-Hash Auth', source:'Windows Security', severity:'HIGH', detail:'NTLM hash from 45.33.2.1 used for CORP\\jdoe' }], relationships:[{ type:'Attacker IP', target:'45.33.2.1', iconType:'network' }, { type:'Target DB', target:'DB-SRV-01', iconType:'server' }], playbook:'AD_ELEVATION_RESPONSE' },
  'DB-SRV-01': { entity:'DB-SRV-01', type:'Database Server', risk_score:80, source_ip:'10.0.0.20', attack_type:'Data Exfiltration', related_incidents:['inc_102'], affected_users:['CORP\\jdoe'], related_events:[{ id:1, timestamp:new Date(Date.now()-5400000).toISOString(), type:'SQL Dump via sqlcmd.exe', source:'DLP', severity:'HIGH', detail:'2.1GB exfiltrated from customer_db' }], relationships:[{ type:'Session Source', target:'APP-SRV-02', iconType:'server' }, { type:'User', target:'CORP\\jdoe', iconType:'user' }], playbook:'AD_ELEVATION_RESPONSE' },
  '185.15.202.13': { entity:'185.15.202.13', type:'C2 Server', risk_score:99, attack_type:'Command & Control', related_incidents:['inc_101'], related_events:[{ id:1, timestamp:new Date(Date.now()-4800000).toISOString(), type:'C2 Beacon', source:'Firewall', severity:'CRITICAL', detail:'Outbound HTTPS from 10.0.5.22 — Cobalt Strike C2 (Rostelecom, RU, ASN12389)' }], relationships:[{ type:'Victim Host', target:'WKS-112-X', iconType:'server' }, { type:'ASN', target:'Rostelecom-RU', iconType:'globe' }], playbook:null },
  'CORP\\svc_admin_temp': { entity:'CORP\\svc_admin_temp', type:'Service Account', risk_score:93, source_ip:'10.0.5.22', attack_type:'Privilege Abuse', related_incidents:['inc_101'], related_events:[{ id:1, timestamp:new Date(Date.now()-3600000).toISOString(), type:'Token Impersonation', source:'Windows Security', severity:'CRITICAL', detail:'SeImpersonatePrivilege → SYSTEM via jsmith session' }], relationships:[{ type:'Impersonated By', target:'CORP\\jsmith', iconType:'user' }, { type:'Host', target:'WKS-112-X', iconType:'server' }], playbook:'RANSOMWARE_RESPONSE' },
  'CORP\\jdoe': { entity:'CORP\\jdoe', type:'User', risk_score:77, source_ip:'45.33.2.1', attack_type:'Compromised Account', related_incidents:['inc_102'], affected_hosts:['APP-SRV-02','DB-SRV-01'], related_events:[{ id:1, timestamp:new Date(Date.now()-7200000).toISOString(), type:'Pass-the-Hash Auth', source:'Windows Security', severity:'HIGH', detail:'NTLM hash reuse — jdoe auth without password' }], relationships:[{ type:'Primary Host', target:'APP-SRV-02', iconType:'server' }, { type:'Source IP', target:'45.33.2.1', iconType:'network' }], playbook:'AD_ELEVATION_RESPONSE' },
};

// Merge so all lookups go through one object
Object.assign(MOCK_ENTITIES, EXTRA_ENTITIES);


// Incident status persistence (overrides mock/real data)
const INCIDENT_STATUS_KEY = 'sentinel_incident_status';
const MOCK_CREDS_KEY      = 'sentinel_mock_creds';


const getIncidentStatus = (id: string, fallback: string) => {
  const store = JSON.parse(localStorage.getItem(INCIDENT_STATUS_KEY) || '{}');
  return store[id] || fallback;
};


// Mock data generator for testuser
const getMockData = (endpoint: string) => {
  const df = getActiveDeviceFilter();
  const filterByIp = (items: any[]) => {
    if (!df) return items;
    return items.filter(i => df.includes(i.source_ip));
  };

  if (endpoint.includes('/api/incidents')) {
    const raw = [
      { id: 'inc_101', severity_label: 'CRITICAL', source_ip: '10.0.5.22', attack_type: 'Ransomware Activity', playbook: 'RANSOMWARE_RESPONSE', status: getIncidentStatus('inc_101', 'OPEN'), created_at: new Date().toISOString() },
      { id: 'inc_102', severity_label: 'HIGH', source_ip: '45.33.2.1', attack_type: 'Lateral Movement', playbook: 'AD_ELEVATION_RESPONSE', status: getIncidentStatus('inc_102', 'OPEN'), created_at: new Date(Date.now() - 3600000).toISOString() },
      { id: 'inc_103', severity_label: 'MEDIUM', source_ip: '192.168.1.1', attack_type: 'Brute Force', playbook: null, status: getIncidentStatus('inc_103', 'INVESTIGATING'), created_at: new Date(Date.now() - 7200000).toISOString() },
      { id: 'inc_104', severity_label: 'CRITICAL', source_ip: '10.0.5.22', attack_type: 'Privilege Escalation', playbook: 'AD_ELEVATION_RESPONSE', status: getIncidentStatus('inc_104', 'OPEN'), created_at: new Date(Date.now() - 1800000).toISOString() },
      { id: 'inc_105', severity_label: 'HIGH', source_ip: '45.33.2.1', attack_type: 'Data Exfiltration', playbook: null, status: getIncidentStatus('inc_105', 'OPEN'), created_at: new Date(Date.now() - 900000).toISOString() },
    ];
    return { data: { incidents: filterByIp(raw) }};
  }
  if (endpoint.includes('/api/events/stats')) {
    const eps = 4200 + Math.random() * 200;
    const lat = 3.8 + Math.random() * 1.2;
    return { data: { status: 'HEALTHY', events_per_second: parseFloat(eps.toFixed(1)), avg_latency_ms: parseFloat(lat.toFixed(2)), drop_rate_pct: 0 }};
  }
  if (endpoint.includes('/api/dashboard/kpis')) {
    tickLive();
    const df = getActiveDeviceFilter();
    const isTest = isTestUser();
    const baseEvts = isTest ? _liveEventCount : 0;
    const baseAnoms = isTest ? _liveAnomCount : 0;
    const evts = df ? Math.round(baseEvts * (df.length / 6)) : baseEvts;
    const anoms = df ? Math.round(baseAnoms * (df.length / 6)) : baseAnoms;
    
    // Filter base incidents to get actual open count
    const rawIncidents = [
      { id: 'inc_101', source_ip: '10.0.5.22' },
      { id: 'inc_102', source_ip: '45.33.2.1' },
      { id: 'inc_103', source_ip: '192.168.1.1' },
      { id: 'inc_104', source_ip: '10.0.5.22' },
      { id: 'inc_105', source_ip: '45.33.2.1' },
    ];
    const statusStore = JSON.parse(localStorage.getItem(INCIDENT_STATUS_KEY) || '{}');
    const MAX_DEVICES = isTest ? 5 : 6;
    const currentActive = df ? df.length : MAX_DEVICES;
    
    const incidents = [
       { id: 'inc_101', source_ip: '10.0.5.22' },
       { id: 'inc_102', source_ip: '45.33.2.1' },
       { id: 'inc_103', source_ip: '192.168.1.1' },
       { id: 'inc_104', source_ip: '10.0.5.22' },
       { id: 'inc_105', source_ip: '45.33.2.1' },
    ];
    const filteredIncidents = df ? incidents.filter(i => df.includes(i.source_ip)) : incidents;
    const openCount = filteredIncidents.filter(i => statusStore[i.id] !== 'RESOLVED').length;
    const closedCount = filteredIncidents.filter(i => statusStore[i.id] === 'RESOLVED').length;

    // Real-time anomalies list to ensure count matches list
    const rawAnoms = [
      { id: 'anom_1', severity_label: 'CRITICAL', source_ip: '10.0.5.22' },
      { id: 'anom_2', severity_label: 'HIGH', source_ip: '45.33.2.1' },
      { id: 'anom_3', severity_label: 'HIGH', source_ip: '10.0.5.22' },
      { id: 'anom_4', severity_label: 'MEDIUM', source_ip: '192.168.1.1' },
      { id: 'anom_5', severity_label: 'HIGH', source_ip: '45.33.2.1' },
      { id: 'anom_6', severity_label: 'MEDIUM', source_ip: '10.0.1.15' },
      { id: 'anom_7', severity_label: 'LOW', source_ip: '10.0.1.22' },
    ];
    const filteredAnoms = df ? rawAnoms.filter(a => df.includes(a.source_ip)) : rawAnoms;

    return { data: { 
      total_events_24h: df ? Math.round(_liveEventCount * (df.length / MAX_DEVICES)) : _liveEventCount, 
      total_anomalies_24h: filteredAnoms.length, 
      open_incidents: openCount, 
      closed_incidents: closedCount,
      active_devices: currentActive
    }};
  }
  if (endpoint.includes('/api/dashboard/anomalies')) {
    const rawAnoms = [
      { id: 'anom_1', severity_label: 'CRITICAL', threat_type: 'Ransomware Activity', source_ip: '10.0.5.22', severity_score: 0.97, created_at: new Date().toISOString() },
      { id: 'anom_2', severity_label: 'HIGH', threat_type: 'Lateral Movement (Pass-the-Hash)', source_ip: '45.33.2.1', severity_score: 0.78, created_at: new Date(Date.now() - 1200000).toISOString() },
      { id: 'anom_3', severity_label: 'HIGH', threat_type: 'C2 Outbound Connection', source_ip: '10.0.5.22', severity_score: 0.91, created_at: new Date(Date.now() - 1800000).toISOString() },
      { id: 'anom_4', severity_label: 'MEDIUM', threat_type: 'Brute Force (SSH)', source_ip: '192.168.1.1', severity_score: 0.55, created_at: new Date(Date.now() - 2600000).toISOString() },
      { id: 'anom_5', severity_label: 'HIGH', threat_type: 'Privilege Escalation', source_ip: '45.33.2.1', severity_score: 0.84, created_at: new Date(Date.now() - 3400000).toISOString() },
      { id: 'anom_6', severity_label: 'MEDIUM', threat_type: 'Unusual Login Time', source_ip: '10.0.1.15', severity_score: 0.45, created_at: new Date(Date.now() - 4200000).toISOString() },
      { id: 'anom_7', severity_label: 'LOW', threat_type: 'Port Scan Detected', source_ip: '10.0.1.22', severity_score: 0.25, created_at: new Date(Date.now() - 5000000).toISOString() },
    ];
    return { data: filterByIp(rawAnoms) };
  }
  if (endpoint.includes('/api/entity/')) {
    const id = endpoint.split('/').pop() || '';
    const ent = MOCK_ENTITIES[id];
    if (ent && ent.type === 'Incident') {
      return { data: { ...ent, status: getIncidentStatus(id, ent.status || 'OPEN') } };
    }
    return { data: ent };
  }
  if (endpoint.includes('/api/dashboard/stats') || endpoint.includes('/api/dashboard/db-stats')) {
    const isTest = isTestUser();
    return { data: { 
      normalized_events: isTest ? 5340234 : 0, 
      anomalies: isTest ? 854 : 0, 
      incidents: isTest ? 42 : 0, 
      devices: isTest ? 45 : 0, 
      model_registry: isTest ? 2 : 0, 
      feedback_labels: isTest ? 5 : 0, 
      users: isTest ? 4 : 0, 
      agents: isTest ? 4 : 0 
    }};
  }
  if (endpoint.includes('/api/dashboard/health')) {
    return { data: { status: 'HEALTHY', events_per_second: 12.5, avg_latency_ms: 4.2, drop_rate_pct: 0.0 }};
  }
  if (endpoint.includes('/api/dashboard/generate-token')) {
    return { data: { token: 'SENT-' + Math.random().toString(36).slice(2,10).toUpperCase() + '-' + Date.now() }};
  }
  if (endpoint.includes('/api/dashboard/retrain')) {
    return { data: { status: 'ok', events: _liveEventCount, models_retrained: 2, duration_ms: 8234, message: `Ensemble + Autoencoder retrained on ${_liveEventCount.toLocaleString()} events.` }};
  }
  if (endpoint.includes('/api/dashboard/run-drift')) {
    return { data: { status: 'ok', features_checked: 8, drifted: 3, message: 'PSI drift detection complete. 3 features drifted (login_hour, failed_logins, latent_var).' }};
  }
  if (endpoint.includes('/api/dashboard/models')) {
    return { data: [
      { model_name:'ensemble',    model_type:'Isolation Forest + LOF + OCSVM', event_count:1543290, trained_at:new Date(Date.now()-86400000*2).toISOString(), version:'v2.4.1', is_stale:false },
      { model_name:'autoencoder', model_type:'PyTorch Neural Autoencoder',     event_count:1543290, trained_at:new Date(Date.now()-86400000*2).toISOString(), version:'v1.8.0', is_stale:false },
    ]};
  }
  if (endpoint.includes('/api/devices')) {
    return { data: [
      { device_id:'AGT-WIN-01', source_type:'Windows Event Log', ip_address:'10.0.5.22',    is_active:true,  last_seen:new Date(Date.now()-2000).toISOString(),       os_type:'Windows Server 2022' },
      { device_id:'AGT-LIN-02', source_type:'Syslog / Auth',     ip_address:'45.33.2.1',    is_active:true,  last_seen:new Date(Date.now()-12000).toISOString(),      os_type:'Ubuntu 22.04' },
      { device_id:'AGT-NET-01', source_type:'Zeek Network',       ip_address:'192.168.1.1',  is_active:true,  last_seen:new Date(Date.now()-240000).toISOString(),     os_type:'Zeek 6.0' },
      { device_id:'AGT-WIN-02', source_type:'Windows Event Log',  ip_address:'10.0.5.23',    is_active:false, last_seen:new Date(Date.now()-50400000).toISOString(),   os_type:'Windows 10 Pro' },
      { device_id:'AGT-LIN-03', source_type:'Syslog / Auth',     ip_address:'10.0.1.15',    is_active:true,  last_seen:new Date(Date.now()-5000).toISOString(),       os_type:'CentOS 8' },
    ]};
  }
  if (endpoint.includes('/api/dashboard/users')) {
    return { data: [
      { id:'usr_001', username:'admin',    role:'ADMIN',   created_at:new Date(Date.now()-86400000*30).toISOString() },
      { id:'usr_002', username:'testuser', role:'ANALYST', created_at:new Date(Date.now()-86400000*14).toISOString() },
      { id:'usr_003', username:'jsmith',   role:'ANALYST', created_at:new Date(Date.now()-86400000*7).toISOString() },
      { id:'usr_004', username:'jdoe',     role:'VIEWER',  created_at:new Date(Date.now()-86400000*3).toISOString() },
    ]};
  }
  if (endpoint.includes('/api/entity/')) {
    const id = endpoint.split('/').pop() || '';
    const decoded = decodeURIComponent(id);
    let entity = MOCK_ENTITIES[id] || MOCK_ENTITIES[decoded];
    if (entity) {
      const status = getIncidentStatus(entity.entity, entity.status || 'OPEN');
      return { data: { ...entity, status } };
    }
    return null;
  }
  if (endpoint.includes('/api/dashboard/export')) {
    const statusStore = JSON.parse(localStorage.getItem(INCIDENT_STATUS_KEY) || '{}');
    const closed = Object.keys(statusStore).filter(k => statusStore[k] === 'RESOLVED');
    const custom = JSON.parse(localStorage.getItem('sentinel_custom_resolutions') || '{}');
    
    const content = `
================================================================================
AI-SENTINEL SOC EXECUTIVE SUMMARY REPORT
================================================================================
Generated At: ${new Date().toLocaleString()}
Classification: CONFIDENTIAL / INTERNAL USE ONLY

1. INCIDENT OVERVIEW
--------------------------------------------------------------------------------
Total Incidents Tracked: 15
Currently Open:          ${Math.max(0, 15 - closed.length)}
Successfully Resolved:   ${closed.length}
Resolution Rate:         ${((closed.length / 15) * 100).toFixed(1)}%

2. RESOLUTION DETAILS
--------------------------------------------------------------------------------
The following incidents were remediated via AI-Sentinel Playbooks:
${closed.map(id => ` - [${id}] Status: RESOLVED (${custom[id]?.playbook || 'Standard Playbook'}) @ ${custom[id]?.timestamp || 'N/A'}`).join('\n')}

3. SYSTEM HEALTH & TELEMETRY
--------------------------------------------------------------------------------
- Active Devices: 6
- Ingestion Status: STABLE
- Model Integrity: 99.4% (Ensemble v2.4.1)

4. OPERATOR RECOMMENDATIONS
--------------------------------------------------------------------------------
- Review custom resolutions for [${Object.keys(custom).join(', ')}]
- Trigger manual model retraining to incorporate new remediation patterns.
- Export detailed log forensic artifacts for high-severity cases.

--------------------------------------------------------------------------------
END OF REPORT
================================================================================
    `;
    return { data: new Blob([content.trim()], { type: 'text/plain' }) };
  }
  return null;
};

// Lets admin password changes work offline without a backend

const getMockCreds = (): Record<string,{ password: string; role: string }> => {
  try { return JSON.parse(localStorage.getItem(MOCK_CREDS_KEY) || '{}'); } catch { return {}; }
};

const setMockCred = (username: string, password: string, role?: string) => {
  const store = getMockCreds();
  store[username] = { password, role: role || store[username]?.role || 'ANALYST' };
  localStorage.setItem(MOCK_CREDS_KEY, JSON.stringify(store));
};

const setMockRole = (username: string, role: string) => {
  const store = getMockCreds();
  if (store[username]) store[username].role = role;
  else store[username] = { password: '', role };
  localStorage.setItem(MOCK_CREDS_KEY, JSON.stringify(store));
};

// Default mock credentials pre-seeded (overridden by localStorage)
const SEED_CREDS: Record<string, { password: string; role: string }> = {
  admin:    { password: 'admin',    role: 'ADMIN' },
  testuser: { password: 'testuser', role: 'ANALYST' },
  jsmith:   { password: 'jsmith',   role: 'ANALYST' },
  jdoe:     { password: 'jdoe',     role: 'VIEWER' },
};

const resolveCred = (username: string) => {
  const store = getMockCreds();
  // localStorage overrides take priority over seed
  return store[username] || SEED_CREDS[username] || null;
};

const isTestUser = () => localStorage.getItem('sentinel_username') === 'testuser';

// Existing Endpoints wrapped with mock logic
export const login = async (credentials: { username: string; password: string }) => {
  // 1. Try the real backend first
  try {
    const res = await api.post('/api/auth/login', credentials);
    localStorage.setItem('sentinel_username', credentials.username);
    if (res.data?.role) localStorage.setItem('sentinel_role', res.data.role);
    return res;
  } catch {
    // 2. Backend offline — check mock credential store
    const cred = resolveCred(credentials.username);
    if (cred && cred.password === credentials.password) {
      const role = cred.role;
      const token = `mock-${credentials.username}-${Date.now()}`;
      localStorage.setItem('sentinel_token',    token);
      localStorage.setItem('sentinel_username', credentials.username);
      localStorage.setItem('sentinel_role',     role);
      return { data: { access_token: token, role } };
    }
    throw new Error('Invalid credentials');
  }
};

export const updateIncidentStatus = async (id: string | number, status: string) => {
  const idStr = String(id);
  const store = JSON.parse(localStorage.getItem(INCIDENT_STATUS_KEY) || '{}');
  store[idStr] = status;
  localStorage.setItem(INCIDENT_STATUS_KEY, JSON.stringify(store));
  
  // Dispatch event for local reactivity
  window.dispatchEvent(new Event('sentinel_state_change'));

  try {
    return await api.post(`/api/incidents/${id}/status`, { status });
  } catch {
    return { data: { ok: true, note: 'Saved locally' } };
  }
};

export const register = async (credentials: any) => {
  try { return await api.post('/api/auth/register', credentials); }
  catch (e) {
    setMockCred(credentials.username, credentials.password, credentials.role || 'ANALYST');
    return { data: { ok: true, message: 'Saved offline' } };
  }
};

export const getHealth = async () => api.get('/api/health');

export const getIncidents = async () => {
  // 1. Try real API first
  try { 
    const res = await api.get('/api/incidents'); 
    if (res.data?.incidents?.length > 0) {
      // Merge local resolutions to ensure instant feedback
      const statusStore = JSON.parse(localStorage.getItem(INCIDENT_STATUS_KEY) || '{}');
      res.data.incidents = res.data.incidents.map((i: any) => ({
        ...i,
        status: statusStore[String(i.id)] || i.status
      }));
      return res;
    }
  } catch (err) {
    console.error("Failed to fetch real incidents:", err);
  }

  // 2. Fallback to mock data for demo
  if (isTestUser()) return getMockData('/api/incidents') || { data: { incidents: [] } };
  return { data: { incidents: [] } };
};

export const assignIncident = async (id: number, assigned_to: string) => api.post(`/incidents/${id}/assign`, { assigned_to });

export const getIngestionStats = async () => {
  try { return await api.get('/api/dashboard/health'); } catch {}
  return { data: { events_per_second: 0, avg_latency_ms: 0, drop_rate_pct: 0 } };
};

export const getAnomalies = async () => {
  try { 
    const res = await api.get('/api/dashboard/anomalies'); 
    if (res.data?.length > 0) return res;
  } catch {}
  return { data: [] };
};

export const getEvents = async (limit = 1000) => {
  try { return await api.get(`/api/dashboard/events?limit=${limit}`); } catch { return { data: [] }; }
};

export const getKpis = async () => {
  let kpis: any = { total_events_24h: 0, total_anomalies_24h: 0, open_incidents: 0, closed_incidents: 0, active_devices: 0 };
  
  // 1. Try real API first
  try { 
    const res = await api.get('/api/dashboard/kpis'); 
    if (res.data) kpis = { ...res.data };
  } catch (err) {}

  // 3. FORCE correct closed_incidents count based on local status store
  // This ensures the counter matches the "Resolved" section exactly.
  try {
    const statusStore = JSON.parse(localStorage.getItem(INCIDENT_STATUS_KEY) || '{}');
    const closedCount = Object.values(statusStore).filter(s => s === 'RESOLVED' || s === 'FALSE_POSITIVE').length;
    // We use the MAX of the local count and server count to avoid losing data
    kpis.closed_incidents = Math.max(kpis.closed_incidents || 0, closedCount);
  } catch {}

  return { data: kpis };
};

export const exportReport = async () => {
  if (isTestUser()) return getMockData('/api/dashboard/export');
  try { return await api.get('/api/dashboard/export', { responseType: 'blob' }); }
  catch { return getMockData('/api/dashboard/export'); }
};
export const generateToken = async () => {
  if (isTestUser()) return getMockData('/api/dashboard/generate-token') || api.post('/api/dashboard/generate-token');
  return api.post('/api/dashboard/generate-token');
};
export const getMetrics = async () => api.get('/api/metrics');
export const getDevices = async () => {
  if (isTestUser()) return getMockData('/api/dashboard/devices') || { data: [] };
  try { return await api.get('/api/dashboard/devices'); } catch { return { data: [] }; }
};
export const deleteDevice = async (id: string) => {
  // Only use mock success if specifically logged in as 'testuser'
  if (isTestUser()) return { data: { status: 'ok' } };
  return api.delete(`/api/dashboard/devices/${id}`);
};
export const updateDeviceStatus = async (id: string, active: boolean) => {
  if (isTestUser()) return { data: { status: 'ok' } };
  return api.post(`/api/dashboard/devices/${id}/status?active=${active}`);
};
export const retrainModel = async () => {
  const isAdmin = localStorage.getItem('sentinel_role') === 'ADMIN';
  const isTest = isTestUser();
  
  try { 
    const res = await api.post('/api/dashboard/retrain');
    if (res.data?.status === 'ok' || res.data?.status === 'success') return res;
    throw new Error(res.data?.message || 'Retrain returned non-ok status');
  } 
  catch (err) { 
    // If Admin or TestUser is testing offline/broken backend, allow mock success
    if (isAdmin || isTest) {
      return new Promise(r => setTimeout(() => r({ data: { status: 'success', message: 'Model retraining started (Simulation)' } }), 1000));
    }
    return { data: { status: 'error', message: (err as any).message || 'Offline' } }; 
  }
};
export const runDrift = async () => {
  const isAdmin = localStorage.getItem('sentinel_role') === 'ADMIN';
  const isTest = isTestUser();

  try { 
    const res = await api.post('/api/dashboard/run-drift');
    if (res.data?.status === 'ok' || res.data?.status === 'success') return res;
    throw new Error(res.data?.message || 'Drift detection returned non-ok status');
  } 
  catch (err) { 
    if (isAdmin || isTest) {
      return new Promise(r => setTimeout(() => r({ data: { status: 'success', message: 'Drift detection completed (Simulation)' } }), 1000));
    }
    return { data: { status: 'error', message: (err as any).message || 'Offline' } }; 
  }
};
export const getModelRegistry = async () => {
  const isAdmin = localStorage.getItem('sentinel_role') === 'ADMIN';
  if (isTestUser() || isAdmin) {
    const res = await api.get('/api/dashboard/models').catch(() => null);
    if (res?.data && res.data.length > 0) return res;
    // Fallback to mock models if backend empty or offline for Admin/Test
    return { data: [
      { model_name: 'ensemble',    model_type: 'Isolation Forest + LOF + OCSVM', event_count: 1543290, trained_at: new Date(Date.now()-86400000*2).toISOString(), version: 'v2.4.1', is_stale: false },
      { model_name: 'autoencoder', model_type: 'PyTorch Neural Autoencoder',     event_count: 1543290, trained_at: new Date(Date.now()-86400000*2).toISOString(), version: 'v1.8.0', is_stale: false },
    ]};
  }
  try { return await api.get('/api/dashboard/models'); } catch { return { data: [] }; }
};
export const getDrift = async () => {
  try { return await api.get('/api/dashboard/drift'); } catch { return { data: {} }; }
};
export const getEntityTimeline = async (params: any) => api.get('/api/entity-timeline', { params });
export const getUsers = async () => {
  try { 
    const r = await api.get('/api/dashboard/users'); 
    if (Array.isArray(r.data) && r.data.length) return r; 
  } catch {}
  
  // Offline fallback: Merge SEED_CREDS + localStorage to show registered users
  const store = (() => { try { return JSON.parse(localStorage.getItem(MOCK_CREDS_KEY) || '{}'); } catch { return {}; } })();
  const merged = { ...SEED_CREDS, ...store };
  const mockUsers = Object.entries(merged).map(([username, info], i) => ({
    id: `usr_offline_${i}`,
    username,
    role: (info as any).role || 'ANALYST',
    created_at: new Date().toISOString()
  }));
  return { data: mockUsers };
};
export const updateUserRole = async (user_id: string, role: string) => {
  const knownUsers: Record<string,string> = { 'usr_001':'admin','usr_002':'testuser','usr_003':'jsmith','usr_004':'jdoe' };
  const username = knownUsers[user_id] || user_id;
  setMockRole(username, role);

  // If editing self, update active session role immediately
  if (username === localStorage.getItem('sentinel_username')) {
    localStorage.setItem('sentinel_role', role);
  }

  try { return await api.post('/api/dashboard/users/role', { user_id, role }); } 
  catch { return { data: { ok: true, note: 'Saved locally' } }; }
};
export const updateUserPassword = async (user_id: string, password: string) => {
  // Always persist locally so offline logins work immediately
  // user_id is the db id (usr_001) — resolve to username from mock users
  const knownUsers: Record<string,string> = {
    'usr_001':'admin','usr_002':'testuser','usr_003':'jsmith','usr_004':'jdoe'
  };
  const username = knownUsers[user_id] || user_id;
  setMockCred(username, password);
  try { return await api.post('/api/dashboard/users/password', { user_id, password }); }
  catch { return { data: { ok: true, note: 'Saved locally — backend offline' } }; }
};

export const updateUserRoleLocal = (username: string, role: string) => setMockRole(username, role);

export const getStats = async () => {
  const isAdmin = localStorage.getItem('sentinel_role') === 'ADMIN';
  if (isTestUser()) {
    const res = await api.get('/api/dashboard/stats').catch(() => null);
    if (res?.data && Object.keys(res.data).length > 0) return res;
    // Mock stats fallback only for testuser
    return { data: { normalized_events: 5340234, anomalies: 854, incidents: 42, devices: 45, model_registry: 2, feedback_labels: 5, users: 4, agents: 4 }};
  }
  try { return await api.get('/api/dashboard/stats'); } catch { return { data: { normalized_events: 0, anomalies: 0, incidents: 0, devices: 0, model_registry: 0, feedback_labels: 0, users: 0, agents: 0 } }; }
};

export const getEntity = async (id: string) => {
  return getMockData(`/api/entity/${id}`) || api.get(`/api/entity/${id}`);
};

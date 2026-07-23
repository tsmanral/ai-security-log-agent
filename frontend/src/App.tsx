import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';
import CommandCenter from './pages/CommandCenter';
import IncidentDrilldown from './pages/IncidentDrilldown';
import RemediationPlaybook from './pages/RemediationPlaybook';
import LiveStream from './pages/LiveStream';
import Analytics from './pages/Analytics';
import Admin from './pages/Admin';
import Investigate from './pages/Investigate';
import Response from './pages/Response';
import Sources from './pages/Sources';
import Login from './pages/Login';
import ModelAnalytics from './pages/ModelAnalytics';
import ConnectDevice from './pages/ConnectDevice';
import ThreatIntel from './pages/ThreatIntel';
import FeedbackLoop from './pages/FeedbackLoop';
import DeviceBehavior from './pages/DeviceBehavior';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/app" element={<DashboardLayout />}>
          <Route index element={<Navigate to="/app/dashboard" replace />} />
          <Route path="dashboard"             element={<CommandCenter />} />
          <Route path="incident/:id"          element={<IncidentDrilldown />} />
          <Route path="incident/:id/playbook" element={<RemediationPlaybook />} />
          <Route path="stream"                element={<LiveStream />} />
          <Route path="analytics"             element={<Analytics />} />
          <Route path="devices"               element={<DeviceBehavior />} />
          <Route path="models"                element={<ModelAnalytics />} />
          <Route path="intel"                 element={<ThreatIntel />} />
          <Route path="connect"               element={<ConnectDevice />} />
          <Route path="feedback"              element={<FeedbackLoop />} />
          <Route path="admin"                 element={<Admin />} />
          <Route path="investigate"           element={<Investigate />} />
          <Route path="response"              element={<Response />} />
          <Route path="sources"               element={<Sources />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;

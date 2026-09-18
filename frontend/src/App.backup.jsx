import {
  Activity,
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  Gauge,
  GitBranch,
  LayoutDashboard,
  Network,
  Radar,
  RefreshCcw,
  ShieldCheck,
  Sparkles,
  Wrench,
} from "lucide-react";

import { NavLink, Route, Routes } from "react-router-dom";

import Incidents from "./pages/Incidents";
import ServiceMap from "./pages/ServiceMap";
import "./index.css";

const navigation = [
  ["Overview", "/", LayoutDashboard],
  ["Incidents", "/incidents", AlertTriangle],
  ["Service Map", "/service-map", Network],
  ["Anomalies", "/anomalies", Radar],
  ["RCA Intelligence", "/rca", GitBranch],
  ["Predictions", "/predictions", BrainCircuit],
  ["Simulator", "/simulator", RefreshCcw],
  ["SLO Impact", "/impact", Gauge],
  ["Remediation", "/remediation", Wrench],
  ["SentinelGuard", "/sentinelguard", ShieldCheck],
  ["Verification", "/verification", CheckCircle2],
  ["AI Investigator", "/investigator", Sparkles],
];

function ComingSoon({ title }) {
  return (
    <div className="page">
      <div className="eyebrow">SENTINELOPS AI</div>
      <h1>{title}</h1>

      <div className="panel coming-soon">
        <BrainCircuit size={38} />
        <strong>{title}</strong>
        <p>This SentinelOps console module will be connected next.</p>
      </div>
    </div>
  );
}

function Overview() {
  return (
    <div className="page">
      <div className="eyebrow">AUTONOMOUS RELIABILITY INTELLIGENCE</div>
      <h1>Reliability Command Center</h1>

      <div className="overview-hero">
        <div>
          <span>Current incident</span>
          <strong>INC-0001</strong>
          <p>payment-service degradation detected and investigated.</p>
        </div>

        <div>
          <span>SentinelGuard</span>
          <strong className="positive">Approved</strong>
          <p>Controlled remediation safety checks passed.</p>
        </div>

        <div>
          <span>Recovery</span>
          <strong className="positive">Verified</strong>
          <p>Post-remediation health verification succeeded.</p>
        </div>
      </div>

      <div className="panel overview-system-panel">
        <div className="panel-title">Reliability Lifecycle</div>

        <div className="overview-lifecycle">
          {[
            "Sense",
            "Detect",
            "Predict",
            "Correlate",
            "Diagnose",
            "Challenge",
            "Simulate",
            "Prioritize",
            "Guard",
            "Execute",
            "Verify",
            "Learn",
          ].map((stage) => (
            <span key={stage}>{stage}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <Activity size={23} />
          </div>

          <div>
            <div className="brand-name">SentinelOps AI</div>
            <div className="brand-subtitle">Reliability Intelligence</div>
          </div>
        </div>

        <div className="nav-section-label">COMMAND CENTER</div>

        <nav>
          {navigation.map(([label, path, Icon]) => (
            <NavLink
              key={label}
              to={path}
              end={path === "/"}
              className={({ isActive }) =>
                `nav-item ${isActive ? "active" : ""}`
              }
            >
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="system-health">
            <span className="live-dot" />
            Platform operational
          </div>

          <div className="version">SentinelOps v1.0.0</div>
        </div>
      </aside>

      <main className="main">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/incidents" element={<Incidents />} />
          <Route path="/service-map" element={<ServiceMap />} />

          <Route
            path="/anomalies"
            element={<ComingSoon title="Anomaly Intelligence" />}
          />

          <Route
            path="/rca"
            element={<ComingSoon title="RCA Intelligence" />}
          />

          <Route
            path="/predictions"
            element={<ComingSoon title="Failure Prediction" />}
          />

          <Route
            path="/simulator"
            element={<ComingSoon title="Counterfactual Simulator" />}
          />

          <Route
            path="/impact"
            element={<ComingSoon title="SLO & Business Impact" />}
          />

          <Route
            path="/remediation"
            element={<ComingSoon title="Remediation Center" />}
          />

          <Route
            path="/sentinelguard"
            element={<ComingSoon title="SentinelGuard" />}
          />

          <Route
            path="/verification"
            element={<ComingSoon title="Recovery Verification" />}
          />

          <Route
            path="/investigator"
            element={<ComingSoon title="AI Investigator" />}
          />
        </Routes>
      </main>
    </div>
  );
}

export default App;

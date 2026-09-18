import { Activity, BrainCircuit, ChartNoAxesCombined, ClipboardList, Gauge, HeartPulse, Menu, Network, Radar, SearchCheck, ShieldCheck, Sparkles, Terminal, Wrench } from "lucide-react";
import { NavLink } from "react-router-dom";
import { ProvenanceBadge, StatusBadge } from "./ui.jsx";

const nav = [
  ["Mission Control", "/", Activity], ["Service Health", "/services", HeartPulse], ["Telemetry", "/telemetry", Radar], ["Failure Prediction", "/prediction", BrainCircuit], ["Incidents", "/incidents", ClipboardList], ["RCA Intelligence", "/rca", SearchCheck], ["RCA Challenger", "/challenger", ShieldCheck], ["Counterfactuals", "/counterfactuals", ChartNoAxesCombined], ["SLO / Priority", "/priority", Gauge], ["Remediation", "/remediation", Wrench], ["SentinelGuard", "/guard", ShieldCheck], ["Recovery", "/recovery", Terminal], ["Investigation", "/investigation", Sparkles], ["Evidence / Audit", "/evidence", ClipboardList], ["System Status", "/system", Network],
];

export function AppShell({ children, title, snapshot }) {
  return <div className="shell"><aside><div className="brand"><Activity /><div><strong>SentinelOps AI</strong><small>Reliability intelligence</small></div></div><nav>{nav.map(([label, path, Icon]) => <NavLink end={path === "/"} to={path} key={path}><Icon size={16} />{label}</NavLink>)}</nav><footer><ProvenanceBadge label="LOCAL LAB" /><small>Deterministic control center</small></footer></aside><main><header><div><span className="eyebrow">SENTINELOPS RELIABILITY CONTROL CENTER</span><h1>{title}</h1></div><div className="top-status"><ProvenanceBadge label="LOCAL LAB" /><ProvenanceBadge label={snapshot.connection.status} /><StatusBadge status="ready" /></div></header><div className="connection-note"><Menu size={14} />{snapshot.connection.detail}</div>{children}</main></div>;
}

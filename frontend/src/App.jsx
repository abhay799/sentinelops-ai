import { useEffect, useMemo, useState } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { AppShell } from "./components/AppShell.jsx";
import { createDataProvider } from "./providers/index.js";
import { ControlView } from "./pages/Views.jsx";
import { labels } from "./routes.js";
import { scenarioIds } from "./data/scenarios/index.js";

const routes = Object.keys(labels);

function View() {
  const location = useLocation();
  const provider = useMemo(() => {
    const search = location.search || window.location.search;
    return createDataProvider({ mode: new URLSearchParams(search).get("mode") === "demo" ? "demo" : (import.meta.env.VITE_API_BASE ? "local-api" : "demo") });
  }, [location.search]);
  const [scenarioId, setScenarioId] = useState("safe-local-recovery");
  const [snapshot, setSnapshot] = useState(null);
  useEffect(() => { provider.getSnapshot({ scenarioId }).then(setSnapshot); }, [provider, scenarioId]);
  if (!snapshot) return <div className="loading">Loading deterministic local scenario…</div>;
  const path = location.pathname;
  return <AppShell title={labels[path] ?? labels["/"]} snapshot={snapshot}><div className="scenario-picker"><label>DEMO SCENARIO<select value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}>{scenarioIds.map((id) => <option key={id} value={id}>{id.replaceAll("-", " ")}</option>)}</select></label><strong>{snapshot.scenario.title}</strong><small>{snapshot.scenario.summary}</small></div><ControlView path={path} scenario={snapshot.scenario} /></AppShell>;
}

export default function App() { return <Routes>{routes.map((path) => <Route key={path} path={path} element={<View />} />)}<Route path="*" element={<View />} /></Routes>; }


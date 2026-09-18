import { useEffect, useMemo, useState } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { AppShell } from "./components/AppShell.jsx";
import { createDataProvider } from "./providers/index.js";
import { ControlView } from "./pages/Views.jsx";
import { labels } from "./routes.js";

const routes = Object.keys(labels);

function View() {
  const location = useLocation();
  const provider = useMemo(() => createDataProvider({ mode: new URLSearchParams(location.search).get("mode") === "local-api" ? "local-api" : "demo" }), [location.search]);
  const [snapshot, setSnapshot] = useState(null);
  useEffect(() => { provider.getSnapshot().then(setSnapshot); }, [provider]);
  if (!snapshot) return <div className="loading">Loading deterministic local scenario…</div>;
  const path = location.pathname;
  return <AppShell title={labels[path] ?? labels["/"]} snapshot={snapshot}><ControlView path={path} scenario={snapshot.scenario} /></AppShell>;
}

export default function App() { return <Routes>{routes.map((path) => <Route key={path} path={path} element={<View />} />)}<Route path="*" element={<View />} /></Routes>; }

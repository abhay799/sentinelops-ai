import { getScenario } from "../data/scenarios/index.js";

const demoSnapshot = (scenarioId, connection = { status: "NOT CONNECTED", fallback: false, detail: "Deterministic demo provider" }) => ({ scenario: getScenario(scenarioId), connection });

export function createDataProvider({ mode = "demo", fetcher = globalThis.fetch } = {}) {
  if (mode !== "local-api") return { getSnapshot: async ({ scenarioId } = {}) => demoSnapshot(scenarioId) };
  return {
    async getSnapshot({ scenarioId } = {}) {
      try {
        const response = await fetcher(`${import.meta.env.VITE_API_BASE}/capabilities`);
        if (!response.ok) throw new Error(`API status ${response.status}`);
        await response.json();
        return demoSnapshot(scenarioId, { status: "API AVAILABLE", fallback: false, detail: "Backend capabilities endpoint reached; deterministic UI scenario remains active." });
      } catch {
        return demoSnapshot(scenarioId, { status: "NOT CONNECTED", fallback: true, detail: "API unavailable; deterministic demo provider active." });
      }
    },
  };
}



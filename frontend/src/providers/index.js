import { getScenario } from "../data/scenarios/index.js";

const demoSnapshot = (scenarioId, connection = { status: "NOT CONNECTED", fallback: false, detail: "Deterministic demo provider" }) => ({ scenario: getScenario(scenarioId), connection });

export function createDataProvider({ mode = "demo", fetcher = globalThis.fetch } = {}) {
  if (mode !== "local-api") return { getSnapshot: async ({ scenarioId } = {}) => demoSnapshot(scenarioId) };
  return {
    async getSnapshot({ scenarioId } = {}) {
      try {
        const response = await fetcher("http://127.0.0.1:8200/capabilities");
        if (!response.ok) throw new Error(`API status ${response.status}`);
        await response.json();
        return demoSnapshot(scenarioId, { status: "LOCAL API AVAILABLE", fallback: false, detail: "Capabilities endpoint reached; deterministic UI scenario remains active." });
      } catch {
        return demoSnapshot(scenarioId, { status: "NOT CONNECTED", fallback: true, detail: "Local API unavailable; deterministic demo provider active." });
      }
    },
  };
}

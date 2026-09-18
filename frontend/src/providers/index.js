import { demoScenario } from "../data/demoScenario.js";

const demoSnapshot = (connection = { status: "NOT CONNECTED", fallback: false, detail: "Deterministic demo provider" }) => ({ scenario: demoScenario, connection });

export function createDataProvider({ mode = "demo", fetcher = globalThis.fetch } = {}) {
  if (mode !== "local-api") return { getSnapshot: async () => demoSnapshot() };
  return {
    async getSnapshot() {
      try {
        const response = await fetcher("http://127.0.0.1:8200/capabilities");
        if (!response.ok) throw new Error(`API status ${response.status}`);
        await response.json();
        return demoSnapshot({ status: "LOCAL API AVAILABLE", fallback: false, detail: "Capabilities endpoint reached; deterministic UI scenario remains active." });
      } catch {
        return demoSnapshot({ status: "NOT CONNECTED", fallback: true, detail: "Local API unavailable; deterministic demo provider active." });
      }
    },
  };
}

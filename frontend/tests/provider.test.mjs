import assert from "node:assert/strict";
import test from "node:test";

import { createDataProvider } from "../src/providers/index.js";

test("demo provider exposes a deterministic, provenance-labelled scenario", async () => {
  const provider = createDataProvider({ mode: "demo" });
  const snapshot = await provider.getSnapshot();

  assert.equal(snapshot.connection.status, "NOT CONNECTED");
  assert.equal(snapshot.scenario.incident.id, "INC-0001");
  assert.equal(snapshot.scenario.services.length, 7);
  assert.equal(snapshot.scenario.provenance.includes("SYNTHETIC"), true);
});

test("local-api provider falls back to deterministic demo data when unavailable", async () => {
  const provider = createDataProvider({
    mode: "local-api",
    fetcher: async () => {
      throw new Error("offline");
    },
  });
  const snapshot = await provider.getSnapshot();

  assert.equal(snapshot.connection.status, "NOT CONNECTED");
  assert.equal(snapshot.connection.fallback, true);
  assert.equal(snapshot.scenario.provider, "DeterministicGroundedProvider");
});

test("provider switches deterministic scenarios by stable ID", async () => {
  const snapshot = await createDataProvider({ mode: "demo" }).getSnapshot({ scenarioId: "normal-operation" });
  assert.equal(snapshot.scenario.id, "normal-operation");
  assert.equal(snapshot.scenario.incident, null);
});

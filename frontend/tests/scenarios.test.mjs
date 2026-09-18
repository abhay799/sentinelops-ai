import assert from "node:assert/strict";
import test from "node:test";

import { getScenario, scenarioIds } from "../src/data/scenarios/index.js";

test("registry has nine stable deterministic scenarios", () => {
  assert.equal(scenarioIds.length, 9);
  assert.equal(getScenario("safe-local-recovery").id, "safe-local-recovery");
});

test("Guard rejection and human pending cannot execute", () => {
  assert.equal(getScenario("sentinelguard-rejection").execution.allowed, false);
  assert.equal(getScenario("human-authorization-pending").execution.allowed, false);
});

test("only safe recovery executes the configured rollback adapter", () => {
  const executed = scenarioIds.filter((id) => getScenario(id).execution.adapterExecuted);
  assert.deepEqual(executed, ["safe-local-recovery"]);
});

test("traffic shift and restart are never validated execution adapters", () => {
  for (const id of scenarioIds) {
    const scenario = getScenario(id);
    assert.equal(scenario.counterfactuals.find((item) => item.action === "traffic_shift").boundary, "planning only");
    assert.equal(scenario.counterfactuals.find((item) => item.action === "restart").boundary, "planning only");
  }
});

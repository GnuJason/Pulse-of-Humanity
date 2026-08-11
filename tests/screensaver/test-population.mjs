import assert from "node:assert/strict";

import { BASE_CONTINENTS, STATIC_ANCHOR } from "../../apps/screensaver-web/src/population.js";
import { dailyCounts, worldNow } from "../../apps/screensaver-web/src/simulation.js";

const anchorTime = STATIC_ANCHOR.baselineTimestampMs;
const oneSecond = anchorTime + 1000;

assert.equal(worldNow(anchorTime), STATIC_ANCHOR.baselinePopulation);
assert.ok(Math.abs(worldNow(oneSecond) - (STATIC_ANCHOR.baselinePopulation + STATIC_ANCHOR.birthsPerSecond - STATIC_ANCHOR.deathsPerSecond)) < 1e-6);
assert.equal(
	Object.values(BASE_CONTINENTS).reduce((sum, continent) => sum + continent.population, 0),
	STATIC_ANCHOR.baselinePopulation - 3,
);
assert.equal(dailyCounts(anchorTime).birthsToday, 0);
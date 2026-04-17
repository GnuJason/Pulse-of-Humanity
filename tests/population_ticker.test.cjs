const test = require('node:test');
const assert = require('node:assert/strict');

const ticker = require('../static/js/population_ticker.js');

test('normalizeAnchor computes the expected net rate', () => {
  const anchor = ticker.normalizeAnchor({
    baselinePopulation: 8000000000,
    baselineTimestamp: '2026-03-30T00:00:00Z',
    birthsPerSecond: 4.3,
    deathsPerSecond: 1.8,
    serverTimestamp: '2026-03-30T00:00:05Z',
    source: 'test',
  }, 0);

  assert.equal(anchor.netPerSecond, 2.5);
  assert.equal(anchor.baselineTimestampMs, Date.parse('2026-03-30T00:00:00Z'));
});

test('computeWorldPopulation uses the deterministic elapsed-time formula', () => {
  const anchor = ticker.normalizeAnchor({
    baselinePopulation: 8000000000,
    baselineTimestamp: '2026-03-30T00:00:00Z',
    birthsPerSecond: 4.3,
    deathsPerSecond: 1.8,
    serverTimestamp: '2026-03-30T00:00:00Z',
    source: 'test',
  }, 0);

  const tenSecondsLater = Date.parse('2026-03-30T00:00:10Z');
  const twentySecondsLater = Date.parse('2026-03-30T00:00:20Z');

  assert.equal(Math.floor(ticker.computeWorldPopulation(anchor, tenSecondsLater)), 8000000025);
  assert.equal(Math.floor(ticker.computeWorldPopulation(anchor, twentySecondsLater)), 8000000050);
});

test('computeDailyCounts resets at UTC midnight', () => {
  const anchor = ticker.normalizeAnchor({
    baselinePopulation: 8000000000,
    baselineTimestamp: '2026-03-30T00:00:00Z',
    birthsPerSecond: 4.3,
    deathsPerSecond: 1.8,
    serverTimestamp: '2026-03-30T00:00:00Z',
    source: 'test',
  }, 0);

  const beforeMidnight = ticker.computeDailyCounts(anchor, Date.parse('2026-03-30T23:59:59Z'));
  const afterMidnight = ticker.computeDailyCounts(anchor, Date.parse('2026-03-31T00:00:01Z'));

  assert.ok(beforeMidnight.birthsToday > afterMidnight.birthsToday);
  assert.equal(Math.floor(afterMidnight.birthsToday), 4);
  assert.equal(Math.floor(afterMidnight.deathsToday), 1);
});

test('computeContinentState is deterministic across clients given the same anchor and authoritative time', () => {
  const rawAnchor = {
    baselinePopulation: 8100000000,
    baselineTimestamp: '2026-03-30T01:00:00Z',
    birthsPerSecond: 4.3,
    deathsPerSecond: 1.8,
    serverTimestamp: '2026-03-30T01:00:02Z',
    source: 'un_wpp',
  };
  const clientOne = ticker.normalizeAnchor(rawAnchor, 25);
  const clientTwo = ticker.normalizeAnchor(rawAnchor, 25);
  const continentModel = {
    baselineShare: 0.17875143936763047,
    birthShare: 0.28571428571428575,
    deathShare: 0.1754385964912281,
  };
  const authoritativeNow = Date.parse('2026-03-30T01:05:00Z');

  assert.deepEqual(
    ticker.computeContinentState(clientOne, continentModel, authoritativeNow),
    ticker.computeContinentState(clientTwo, continentModel, authoritativeNow)
  );
});

test('computeClockOffset uses the request midpoint to reduce network skew', () => {
  const offset = ticker.computeClockOffset(new Date(20010).toISOString(), 20020, 20060);

  assert.equal(offset, 30);
});
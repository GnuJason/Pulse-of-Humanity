(function (global) {
  "use strict";

  var MS_PER_SECOND = 1000;

  function parseTimestamp(timestamp) {
    return Date.parse(timestamp);
  }

  function computeClockOffset(serverTimestamp, requestStartedAtMs, responseReceivedAtMs) {
    var serverTimestampMs = parseTimestamp(serverTimestamp);
    var midpointMs = requestStartedAtMs + ((responseReceivedAtMs - requestStartedAtMs) / 2);
    return midpointMs - serverTimestampMs;
  }

  function normalizeAnchor(anchor, clockOffsetMs) {
    return {
      baselinePopulation: Number(anchor.baselinePopulation),
      baselineTimestamp: anchor.baselineTimestamp,
      baselineTimestampMs: parseTimestamp(anchor.baselineTimestamp),
      birthsPerSecond: Number(anchor.birthsPerSecond),
      deathsPerSecond: Number(anchor.deathsPerSecond),
      netPerSecond: Number(anchor.birthsPerSecond) - Number(anchor.deathsPerSecond),
      serverTimestamp: anchor.serverTimestamp,
      serverTimestampMs: parseTimestamp(anchor.serverTimestamp),
      source: anchor.source,
      clockOffsetMs: Number(clockOffsetMs),
    };
  }

  function getAuthoritativeNow(clockOffsetMs, clientNowMs) {
    return Number(clientNowMs || Date.now()) - Number(clockOffsetMs);
  }

  function getElapsedSeconds(anchor, authoritativeNowMs) {
    return Math.max(0, (Number(authoritativeNowMs) - Number(anchor.baselineTimestampMs)) / MS_PER_SECOND);
  }

  function getUtcDayStart(authoritativeNowMs) {
    var current = new Date(authoritativeNowMs);
    return Date.UTC(
      current.getUTCFullYear(),
      current.getUTCMonth(),
      current.getUTCDate(),
      0,
      0,
      0,
      0
    );
  }

  function getSecondsSinceUtcMidnight(authoritativeNowMs) {
    return Math.max(0, (Number(authoritativeNowMs) - getUtcDayStart(authoritativeNowMs)) / MS_PER_SECOND);
  }

  function computeWorldPopulation(anchor, authoritativeNowMs) {
    return anchor.baselinePopulation + (getElapsedSeconds(anchor, authoritativeNowMs) * anchor.netPerSecond);
  }

  function computeDailyCounts(anchor, authoritativeNowMs) {
    var secondsToday = getSecondsSinceUtcMidnight(authoritativeNowMs);
    return {
      birthsToday: secondsToday * anchor.birthsPerSecond,
      deathsToday: secondsToday * anchor.deathsPerSecond,
    };
  }

  function computeContinentState(anchor, continentModel, authoritativeNowMs) {
    var elapsedSeconds = getElapsedSeconds(anchor, authoritativeNowMs);
    var secondsToday = getSecondsSinceUtcMidnight(authoritativeNowMs);
    var birthsPerSecond = Number(continentModel.birthShare) * anchor.birthsPerSecond;
    var deathsPerSecond = Number(continentModel.deathShare) * anchor.deathsPerSecond;

    return {
      population: (Number(continentModel.baselineShare) * anchor.baselinePopulation) + ((birthsPerSecond - deathsPerSecond) * elapsedSeconds),
      birthsToday: Number(continentModel.birthShare) * anchor.birthsPerSecond * secondsToday,
      deathsToday: Number(continentModel.deathShare) * anchor.deathsPerSecond * secondsToday,
      birthsPerSecond: birthsPerSecond,
      deathsPerSecond: deathsPerSecond,
    };
  }

  var api = {
    computeClockOffset: computeClockOffset,
    normalizeAnchor: normalizeAnchor,
    getAuthoritativeNow: getAuthoritativeNow,
    getElapsedSeconds: getElapsedSeconds,
    computeWorldPopulation: computeWorldPopulation,
    computeDailyCounts: computeDailyCounts,
    computeContinentState: computeContinentState,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }

  global.PopulationTicker = api;
}(typeof window !== "undefined" ? window : globalThis));
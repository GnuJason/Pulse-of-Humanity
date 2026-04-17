"""Population model: annual authoritative anchoring and deterministic demographic simulation."""

import calendar
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


STATE_PATH = Path("state.json")
STATE_LOCK = threading.Lock()
UPDATER_THREAD_LOCK = threading.Lock()
UPDATER_THREAD = None

BASE_CONTINENTS = {
    "Africa": {"population": 1420000000, "births_per_sec": 2.7, "deaths_per_sec": 0.9},
    "Asia": {"population": 4700000000, "births_per_sec": 4.5, "deaths_per_sec": 2.1},
    "Europe": {"population": 750000000, "births_per_sec": 0.9, "deaths_per_sec": 1.1},
    "North_America": {"population": 600000000, "births_per_sec": 0.7, "deaths_per_sec": 0.6},
    "South_America": {"population": 430000000, "births_per_sec": 0.6, "deaths_per_sec": 0.4},
    "Oceania": {"population": 44000000, "births_per_sec": 0.05, "deaths_per_sec": 0.03},
    "Antarctica": {"population": 1100, "births_per_sec": 0.0, "deaths_per_sec": 0.0},
}

_CACHE = {"anchor": None, "year": None, "ts": 0.0}
CACHE_TTL = int(os.getenv("POP_CACHE_TTL", "3600"))
ANCHOR_CHECK_INTERVAL_SECONDS = int(os.getenv("POP_ANCHOR_CHECK_INTERVAL", "30"))
STATE_SCHEMA_VERSION = 5

ANCHOR_MONTH = int(os.getenv("POP_ANCHOR_MONTH", "1"))
ANCHOR_DAY = int(os.getenv("POP_ANCHOR_DAY", "1"))

BIRTHS_PER_SEC = 4.28
DEATHS_PER_SEC = 2.06
NET_PER_SEC = BIRTHS_PER_SEC - DEATHS_PER_SEC

STATIC_ANCHOR = {
    "baseline_population": 8130371000,
    "baseline_timestamp": "2026-01-01T00:00:00Z",
    "births_per_second": BIRTHS_PER_SEC,
    "deaths_per_second": DEATHS_PER_SEC,
    "source": "UN WPP 2024 Medium Variant (static)",
    "last_anchor_year": 2026,
}


def utc_now():
    return datetime.now(timezone.utc)


def isoformat_z(value):
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_timestamp(value):
    if not value:
        return utc_now()
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def midnight_utc():
    now = utc_now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def seconds_in_year(year):
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    return (end - start).total_seconds()


def get_anchor_date(year):
    last_day = calendar.monthrange(year, ANCHOR_MONTH)[1]
    anchor_day = min(ANCHOR_DAY, last_day)
    return datetime(year, ANCHOR_MONTH, anchor_day, tzinfo=timezone.utc)


def get_effective_anchor_year(now=None):
    now = now or utc_now()
    current_year_anchor = get_anchor_date(now.year)
    return now.year if now >= current_year_anchor else now.year - 1


def normalize_named_distribution(raw_values):
    total = sum(max(0.0, float(raw_values.get(name, 0.0))) for name in BASE_CONTINENTS)
    if total <= 0:
        equal_share = 1.0 / len(BASE_CONTINENTS)
        return {name: equal_share for name in BASE_CONTINENTS}

    normalized = {
        name: max(0.0, float(raw_values.get(name, 0.0))) / total
        for name in BASE_CONTINENTS
    }
    last_name = list(BASE_CONTINENTS)[-1]
    normalized[last_name] += 1.0 - sum(normalized.values())
    return normalized


def build_share_model(populations=None, birth_rates=None, death_rates=None):
    populations = populations or {
        name: data["population"] for name, data in BASE_CONTINENTS.items()
    }
    birth_rates = birth_rates or {
        name: data["births_per_sec"] for name, data in BASE_CONTINENTS.items()
    }
    death_rates = death_rates or {
        name: data["deaths_per_sec"] for name, data in BASE_CONTINENTS.items()
    }

    baseline_shares = normalize_named_distribution(populations)
    birth_shares = normalize_named_distribution(birth_rates)
    death_shares = normalize_named_distribution(death_rates)

    return {
        name: {
            "baseline_share": baseline_shares[name],
            "birth_share": birth_shares[name],
            "death_share": death_shares[name],
        }
        for name in BASE_CONTINENTS
    }


def canonicalize_share_state(continents_state):
    default_share_model = build_share_model()
    baseline_shares = normalize_named_distribution({
        name: continents_state.get(name, {}).get(
            "baseline_share", default_share_model[name]["baseline_share"]
        )
        for name in BASE_CONTINENTS
    })
    birth_shares = normalize_named_distribution({
        name: continents_state.get(name, {}).get(
            "birth_share", default_share_model[name]["birth_share"]
        )
        for name in BASE_CONTINENTS
    })
    death_shares = normalize_named_distribution({
        name: continents_state.get(name, {}).get(
            "death_share", default_share_model[name]["death_share"]
        )
        for name in BASE_CONTINENTS
    })

    return {
        name: {
            "baseline_share": baseline_shares[name],
            "birth_share": birth_shares[name],
            "death_share": death_shares[name],
        }
        for name in BASE_CONTINENTS
    }


def reconcile_integer_distribution(total, raw_values):
    total = max(0, int(total))
    integer_values = {
        name: max(0, int(raw_values.get(name, 0.0)))
        for name in BASE_CONTINENTS
    }
    remainder = total - sum(integer_values.values())
    if remainder <= 0:
        return integer_values

    ranked_names = sorted(
        BASE_CONTINENTS,
        key=lambda name: (raw_values.get(name, 0.0) - integer_values[name], name),
        reverse=True,
    )
    for index in range(remainder):
        integer_values[ranked_names[index % len(ranked_names)]] += 1
    return integer_values


def reanchor_continent_shares(state, current_state):
    baseline_shares = normalize_named_distribution({
        name: current_state["continents"][name]["population"]
        for name in BASE_CONTINENTS
    })
    birth_shares = normalize_named_distribution({
        name: state["continents"][name]["birth_share"]
        for name in BASE_CONTINENTS
    })
    death_shares = normalize_named_distribution({
        name: state["continents"][name]["death_share"]
        for name in BASE_CONTINENTS
    })
    return {
        name: {
            "baseline_share": baseline_shares[name],
            "birth_share": birth_shares[name],
            "death_share": death_shares[name],
        }
        for name in BASE_CONTINENTS
    }


def get_static_anchor():
    return {
        "population": int(STATIC_ANCHOR["baseline_population"]),
        "births_per_second": float(STATIC_ANCHOR["births_per_second"]),
        "deaths_per_second": float(STATIC_ANCHOR["deaths_per_second"]),
        "source": STATIC_ANCHOR["source"],
        "anchor_year": int(STATIC_ANCHOR["last_anchor_year"]),
        "data_year": int(STATIC_ANCHOR["last_anchor_year"]),
    }


def get_authoritative_population_anchor(target_year=None, allow_fallback=True):
    target_year = int(STATIC_ANCHOR["last_anchor_year"])
    now = time.time()
    cached_anchor = _CACHE.get("anchor")
    if cached_anchor and _CACHE.get("year") == target_year and (now - _CACHE.get("ts", 0.0) < CACHE_TTL):
        return dict(cached_anchor)

    anchor = get_static_anchor()
    _CACHE.update({"anchor": dict(anchor), "year": target_year, "ts": now})
    return anchor


def get_population_cached(target_year=None):
    anchor = get_authoritative_population_anchor(target_year=target_year, allow_fallback=True)
    return anchor["population"], anchor["source"]


def build_initial_state(
    now=None,
    baseline_population=None,
    source="fallback",
    births_per_second=None,
    deaths_per_second=None,
    anchor_year=None,
    baseline_timestamp=None,
):
    now = now or utc_now()
    anchor_year = int(anchor_year if anchor_year is not None else STATIC_ANCHOR["last_anchor_year"])

    if baseline_population is None:
        anchor = get_authoritative_population_anchor(target_year=anchor_year, allow_fallback=True)
        baseline_population = anchor["population"]
        births_per_second = anchor["births_per_second"]
        deaths_per_second = anchor["deaths_per_second"]
        source = anchor["source"]
        anchor_year = anchor["anchor_year"]
        baseline_timestamp = STATIC_ANCHOR["baseline_timestamp"]

    if births_per_second is None:
        births_per_second = BIRTHS_PER_SEC
    if deaths_per_second is None:
        deaths_per_second = DEATHS_PER_SEC

    return {
        "version": STATE_SCHEMA_VERSION,
        "baseline_population": int(baseline_population),
        "baseline_timestamp": baseline_timestamp or isoformat_z(get_anchor_date(anchor_year)),
        "births_per_second": float(births_per_second),
        "deaths_per_second": float(deaths_per_second),
        "source": source,
        "last_anchor_year": anchor_year,
        "continents": build_share_model(),
    }


def migrate_state(state):
    baseline_timestamp = state.get("baseline_timestamp") or state.get("last_updated") or isoformat_z(utc_now())
    legacy_continents = state.get("continents", {})
    share_model = build_share_model(
        populations={
            name: float(
                legacy_continents.get(name, {}).get(
                    "population",
                    legacy_continents.get(name, {}).get("baseline_population", data["population"]),
                )
            )
            for name, data in BASE_CONTINENTS.items()
        },
        birth_rates={
            name: float(legacy_continents.get(name, {}).get("births_per_sec", data["births_per_sec"]))
            for name, data in BASE_CONTINENTS.items()
        },
        death_rates={
            name: float(legacy_continents.get(name, {}).get("deaths_per_sec", data["deaths_per_sec"]))
            for name, data in BASE_CONTINENTS.items()
        },
    )
    baseline_dt = parse_timestamp(baseline_timestamp)
    source = state.get("source", "migrated")
    return {
        "version": STATE_SCHEMA_VERSION,
        "baseline_population": int(state.get("baseline_population", state.get("population", STATIC_ANCHOR["baseline_population"]))),
        "baseline_timestamp": isoformat_z(baseline_dt),
        "births_per_second": float(state.get("births_per_second", BIRTHS_PER_SEC)),
        "deaths_per_second": float(state.get("deaths_per_second", DEATHS_PER_SEC)),
        "source": source,
        "last_anchor_year": int(state.get("last_anchor_year", STATIC_ANCHOR["last_anchor_year"])),
        "continents": share_model,
    }


def ensure_state_shape(state):
    if state.get("version") != STATE_SCHEMA_VERSION or "baseline_population" not in state:
        state = migrate_state(state)

    baseline_timestamp = state.get("baseline_timestamp", STATIC_ANCHOR["baseline_timestamp"])
    baseline_dt = parse_timestamp(baseline_timestamp)
    return {
        "version": STATE_SCHEMA_VERSION,
        "baseline_population": int(state.get("baseline_population", STATIC_ANCHOR["baseline_population"])),
        "baseline_timestamp": isoformat_z(baseline_dt),
        "births_per_second": float(state.get("births_per_second", BIRTHS_PER_SEC)),
        "deaths_per_second": float(state.get("deaths_per_second", DEATHS_PER_SEC)),
        "source": state.get("source", STATIC_ANCHOR["source"]),
        "last_anchor_year": int(state.get("last_anchor_year", STATIC_ANCHOR["last_anchor_year"])),
        "continents": canonicalize_share_state(state.get("continents", {})),
    }


def calculate_current_state(state, now=None):
    now = now or utc_now()
    baseline_timestamp = parse_timestamp(state["baseline_timestamp"])
    elapsed_seconds = max(0.0, (now - baseline_timestamp).total_seconds())
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_today = max(0.0, (now - midnight).total_seconds())

    baseline_population = float(state["baseline_population"])
    births_per_second = float(state.get("births_per_second", BIRTHS_PER_SEC))
    deaths_per_second = float(state.get("deaths_per_second", DEATHS_PER_SEC))
    population = max(0.0, baseline_population + ((births_per_second - deaths_per_second) * elapsed_seconds))
    births_today = births_per_second * seconds_today
    deaths_today = deaths_per_second * seconds_today
    current_state = {
        "population": population,
        "births_today": births_today,
        "deaths_today": deaths_today,
        "last_updated": isoformat_z(now),
        "source": state.get("source", STATIC_ANCHOR["source"]),
        "baseline_timestamp": state["baseline_timestamp"],
        "births_per_second": births_per_second,
        "deaths_per_second": deaths_per_second,
        "last_anchor_year": int(state.get("last_anchor_year", STATIC_ANCHOR["last_anchor_year"])),
        "continents": {},
    }

    for name in BASE_CONTINENTS:
        continent_state = state["continents"][name]
        baseline_continent_population = continent_state["baseline_share"] * baseline_population
        share = 0.0 if baseline_population <= 0 else (baseline_continent_population / baseline_population)
        births_per_sec = share * births_per_second
        deaths_per_sec = share * deaths_per_second
        current_state["continents"][name] = {
            "population": max(0.0, baseline_continent_population + ((births_per_sec - deaths_per_sec) * elapsed_seconds)),
            "births_today": births_per_sec * seconds_today,
            "deaths_today": deaths_per_sec * seconds_today,
            "births_per_sec": births_per_sec,
            "deaths_per_sec": deaths_per_sec,
        }

    return current_state


def serialize_current_state(current_state):
    total_population = int(current_state["population"])
    total_births = int(current_state["births_today"])
    total_deaths = int(current_state["deaths_today"])
    population_distribution = reconcile_integer_distribution(
        total_population,
        {name: data["population"] for name, data in current_state["continents"].items()},
    )
    births_distribution = reconcile_integer_distribution(
        total_births,
        {name: data["births_today"] for name, data in current_state["continents"].items()},
    )
    deaths_distribution = reconcile_integer_distribution(
        total_deaths,
        {name: data["deaths_today"] for name, data in current_state["continents"].items()},
    )

    return {
        "population": total_population,
        "births_today": total_births,
        "deaths_today": total_deaths,
        "last_updated": current_state["last_updated"],
        "source": current_state["source"],
        "baseline_timestamp": current_state["baseline_timestamp"],
        "births_per_second": current_state["births_per_second"],
        "deaths_per_second": current_state["deaths_per_second"],
        "last_anchor_year": current_state["last_anchor_year"],
        "continents": {
            name: {
                "population": population_distribution[name],
                "births_today": births_distribution[name],
                "deaths_today": deaths_distribution[name],
                "births_per_sec": data["births_per_sec"],
                "deaths_per_sec": data["deaths_per_sec"],
            }
            for name, data in current_state["continents"].items()
        },
    }


def serialize_live_state_contract(state, now=None):
    now = now or utc_now()
    current_state = serialize_current_state(calculate_current_state(state, now=now))
    return {
        "baselinePopulation": int(state["baseline_population"]),
        "baselineTimestamp": state["baseline_timestamp"],
        "birthsPerSecond": float(state.get("births_per_second", BIRTHS_PER_SEC)),
        "deathsPerSecond": float(state.get("deaths_per_second", DEATHS_PER_SEC)),
        "serverTimestamp": isoformat_z(now),
        "source": state.get("source", STATIC_ANCHOR["source"]),
        "lastAnchorYear": int(state.get("last_anchor_year", STATIC_ANCHOR["last_anchor_year"])),
        "continents": {
            name: {
                "population": int(data["population"]),
                "birthsPerSecond": float(data["births_per_sec"]),
                "deathsPerSecond": float(data["deaths_per_sec"]),
                "birthsToday": int(data["births_today"]),
                "deathsToday": int(data["deaths_today"]),
            }
            for name, data in current_state["continents"].items()
        },
    }


def serialize_continent_model(state):
    baseline_population = float(state.get("baseline_population", STATIC_ANCHOR["baseline_population"]))
    births_per_second = float(state.get("births_per_second", BIRTHS_PER_SEC))
    deaths_per_second = float(state.get("deaths_per_second", DEATHS_PER_SEC))
    return {
        name: {
            "baselineShare": continent_state["baseline_share"],
            "population": int(continent_state["baseline_share"] * baseline_population),
            "birthsPerSecond": continent_state["baseline_share"] * births_per_second,
            "deathsPerSecond": continent_state["baseline_share"] * deaths_per_second,
        }
        for name, continent_state in state["continents"].items()
    }


def load_state():
    if STATE_PATH.exists():
        with STATE_PATH.open("r") as handle:
            state = json.load(handle)
        state = ensure_state_shape(state)
        save_state(state)
        return state

    state = build_initial_state(now=utc_now())
    save_state(state)
    return state


def save_state(state):
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_PATH.with_suffix(".tmp")
        with tmp.open("w") as handle:
            json.dump(state, handle)
        tmp.replace(STATE_PATH)
    except Exception as exc:
        print(f"[ERROR] Failed to save state: {exc}")
        try:
            with STATE_PATH.open("w") as handle:
                json.dump(state, handle)
        except Exception as fallback_exc:
            print(f"[ERROR] Failed direct state save: {fallback_exc}")


def state_uses_static_anchor(state):
    return (
        int(state.get("baseline_population", 0)) == int(STATIC_ANCHOR["baseline_population"])
        and state.get("baseline_timestamp") == STATIC_ANCHOR["baseline_timestamp"]
        and float(state.get("births_per_second", 0.0)) == float(STATIC_ANCHOR["births_per_second"])
        and float(state.get("deaths_per_second", 0.0)) == float(STATIC_ANCHOR["deaths_per_second"])
        and state.get("source") == STATIC_ANCHOR["source"]
        and int(state.get("last_anchor_year", 0)) == int(STATIC_ANCHOR["last_anchor_year"])
    )


def refresh_population_baseline(force=False, now=None, target_year=None):
    now = now or utc_now()
    desired_anchor_year = int(STATIC_ANCHOR["last_anchor_year"])

    with STATE_LOCK:
        state = load_state()
        needs_refresh = force or state.get("source") == "migrated" or not state_uses_static_anchor(state)
        if not needs_refresh:
            return False

        anchor = get_authoritative_population_anchor(target_year=desired_anchor_year, allow_fallback=True)
        current_state = calculate_current_state(state, now=now)
        state["baseline_population"] = int(anchor["population"])
        state["baseline_timestamp"] = STATIC_ANCHOR["baseline_timestamp"]
        state["births_per_second"] = float(anchor["births_per_second"])
        state["deaths_per_second"] = float(anchor["deaths_per_second"])
        state["source"] = anchor["source"]
        state["last_anchor_year"] = desired_anchor_year
        state["continents"] = reanchor_continent_shares(state, current_state)
        save_state(state)
        return True


def updater_loop():
    while True:
        try:
            refresh_population_baseline()
        except Exception as exc:
            print(f"[ERROR] Annual anchor refresh failed: {exc}")
        time.sleep(max(1, ANCHOR_CHECK_INTERVAL_SECONDS))


def start_updater():
    global UPDATER_THREAD
    with UPDATER_THREAD_LOCK:
        if UPDATER_THREAD is not None and UPDATER_THREAD.is_alive():
            return False

        UPDATER_THREAD = threading.Thread(target=updater_loop, daemon=True, name="population-anchor-updater")
        UPDATER_THREAD.start()
        return True


def get_current_state(now=None):
    refresh_population_baseline(force=False, now=now)
    with STATE_LOCK:
        state = load_state()
        return calculate_current_state(state, now=now)


def get_authoritative_state(now=None):
    refresh_population_baseline(force=False, now=now)
    with STATE_LOCK:
        return load_state()


def get_live_state_contract(now=None):
    refresh_population_baseline(force=False, now=now)
    with STATE_LOCK:
        state = load_state()
        return serialize_live_state_contract(state, now=now)


def current_population_and_today():
    state = get_current_state()
    return (
        int(state["population"]),
        int(state["births_today"]),
        int(state["deaths_today"]),
        state["last_updated"],
    )

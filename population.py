"""Population model: data fetching, state management, and demographic calculations."""

import json
import os
import re
import threading
import time
import datetime as dt
from datetime import datetime, timezone
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
STATE_PATH = Path("state.json")
STATE_LOCK = threading.Lock()

BASE_CONTINENTS = {
    "Africa":        {"population": 1420000000, "births_per_sec": 2.7, "deaths_per_sec": 0.9},
    "Asia":          {"population": 4700000000, "births_per_sec": 4.5, "deaths_per_sec": 2.1},
    "Europe":        {"population":  750000000, "births_per_sec": 0.9, "deaths_per_sec": 1.1},
    "North_America": {"population":  600000000, "births_per_sec": 0.7, "deaths_per_sec": 0.6},
    "South_America": {"population":  430000000, "births_per_sec": 0.6, "deaths_per_sec": 0.4},
    "Oceania":       {"population":   44000000, "births_per_sec": 0.05, "deaths_per_sec": 0.03},
    "Antarctica":    {"population":       1100, "births_per_sec": 0.0, "deaths_per_sec": 0.0},
}

_CACHE = {"population": None, "source": None, "ts": 0.0}
CACHE_TTL = int(os.getenv("POP_CACHE_TTL", "60"))
SYNC_INTERVAL_SECONDS = int(os.getenv("POP_SYNC_INTERVAL", "3600"))
STATE_SCHEMA_VERSION = 3

UA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (PulseOfHumanity/1.0; +https://example.com)",
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
}

BIRTHS_PER_SEC = 4.3
DEATHS_PER_SEC = 1.8
NET_PER_SEC = BIRTHS_PER_SEC - DEATHS_PER_SEC

# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def get_population_api():
    api_key = os.getenv("API_NINJAS_KEY")
    if not api_key:
        return None
    try:
        r = requests.get(
            "https://api.api-ninjas.com/v1/worldpopulation",
            headers={"X-Api-Key": api_key, **UA_HEADERS},
            timeout=10,
        )
        if r.ok:
            data = r.json()
            pop = data.get("world_population")
            if pop and isinstance(pop, (int, float)) and pop > 0:
                return int(pop)
            else:
                print(f"[WARN] API Ninjas returned invalid population data: {data}")
        else:
            print(f"[ERROR] API Ninjas HTTP {r.status_code}: {r.text[:200]}")
    except requests.exceptions.Timeout:
        print("[ERROR] API Ninjas timeout")
    except Exception as e:
        print("[ERROR] API Ninjas exception:", e)
    return None


def get_population_worldometer():
    try:
        r = requests.get(
            "https://www.worldometers.info/world-population/",
            headers=UA_HEADERS,
            timeout=8,
        )
        match = re.search(
            r'<div class="maincounter-number">\s*<span[^>]*>([\d,]+)</span>',
            r.text,
        )
        if match:
            return int(match.group(1).replace(",", ""))
        else:
            print("[WARN] Worldometer pattern not found")
    except Exception as e:
        print("[ERROR] Worldometer exception:", e)
    return None


def get_population_cached():
    now = time.time()
    if _CACHE["population"] and (now - _CACHE["ts"] < CACHE_TTL):
        return _CACHE["population"], _CACHE["source"]

    pop = get_population_api()
    src = "api_ninjas" if pop else None
    if not pop:
        pop = get_population_worldometer()
        src = "worldometer" if pop else None
    if not pop:
        pop = 8_123_456_789
        src = "fallback"

    _CACHE.update({"population": pop, "source": src, "ts": now})
    return pop, src

# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

def utc_now():
    return datetime.now(timezone.utc)


def isoformat_z(value):
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_timestamp(value):
    if not value:
        return utc_now()
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def midnight_utc():
    now = dt.datetime.utcnow()
    return dt.datetime(now.year, now.month, now.day)

# ---------------------------------------------------------------------------
# Share-model math
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

def build_initial_state(now=None, baseline_population=None, source="fallback"):
    now = now or utc_now()
    if baseline_population is None:
        baseline_population, source = get_population_cached()
    return {
        "version": STATE_SCHEMA_VERSION,
        "baseline_population": int(baseline_population),
        "baseline_timestamp": isoformat_z(now),
        "source": source,
        "last_sync_timestamp": isoformat_z(now),
        "refresh_pending": False,
        "continents": build_share_model(),
    }


def migrate_state(state):
    baseline_timestamp = state.get("last_updated") or isoformat_z(utc_now())
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
    source = state.get("source", "migrated")
    return {
        "version": STATE_SCHEMA_VERSION,
        "baseline_population": int(state.get("population", 8_123_456_789)),
        "baseline_timestamp": baseline_timestamp,
        "source": source,
        "last_sync_timestamp": state.get("last_sync_timestamp", baseline_timestamp),
        "refresh_pending": bool(state.get("refresh_pending", source == "migrated")),
        "continents": share_model,
    }


def ensure_state_shape(state):
    if state.get("version") != STATE_SCHEMA_VERSION or "baseline_population" not in state:
        state = migrate_state(state)

    return {
        "version": STATE_SCHEMA_VERSION,
        "baseline_population": int(state.get("baseline_population", 8_123_456_789)),
        "baseline_timestamp": state.get("baseline_timestamp", isoformat_z(utc_now())),
        "source": state.get("source", "fallback"),
        "last_sync_timestamp": state.get("last_sync_timestamp", state.get("baseline_timestamp", isoformat_z(utc_now()))),
        "refresh_pending": bool(state.get("refresh_pending", state.get("source") == "migrated")),
        "continents": canonicalize_share_state(state.get("continents", {})),
    }

# ---------------------------------------------------------------------------
# Current-state computation
# ---------------------------------------------------------------------------

def calculate_current_state(state, now=None):
    now = now or utc_now()
    baseline_timestamp = parse_timestamp(state["baseline_timestamp"])
    elapsed_seconds = max(0.0, (now - baseline_timestamp).total_seconds())
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_today = max(0.0, (now - midnight).total_seconds())

    baseline_population = float(state["baseline_population"])
    population = max(0.0, baseline_population + (NET_PER_SEC * elapsed_seconds))
    births_today = BIRTHS_PER_SEC * seconds_today
    deaths_today = DEATHS_PER_SEC * seconds_today
    current_state = {
        "population": population,
        "births_today": births_today,
        "deaths_today": deaths_today,
        "last_updated": isoformat_z(now),
        "source": state.get("source", "fallback"),
        "baseline_timestamp": state["baseline_timestamp"],
        "last_sync_timestamp": state.get("last_sync_timestamp", state["baseline_timestamp"]),
        "refresh_pending": bool(state.get("refresh_pending", False)),
        "continents": {},
    }

    for name in BASE_CONTINENTS:
        continent_state = state["continents"][name]
        births_per_sec = continent_state["birth_share"] * BIRTHS_PER_SEC
        deaths_per_sec = continent_state["death_share"] * DEATHS_PER_SEC
        baseline_continent_population = continent_state["baseline_share"] * baseline_population
        current_state["continents"][name] = {
            "population": max(0.0, baseline_continent_population + ((births_per_sec - deaths_per_sec) * elapsed_seconds)),
            "births_today": continent_state["birth_share"] * births_today,
            "deaths_today": continent_state["death_share"] * deaths_today,
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
        "last_sync_timestamp": current_state["last_sync_timestamp"],
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

# ---------------------------------------------------------------------------
# Disk I/O
# ---------------------------------------------------------------------------

def load_state():
    if STATE_PATH.exists():
        with STATE_PATH.open("r") as f:
            state = json.load(f)
        state = ensure_state_shape(state)
        save_state(state)
        return state

    pop, source = get_population_cached()
    state = build_initial_state(now=utc_now(), baseline_population=pop, source=source)
    save_state(state)
    return state


def save_state(state):
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_PATH.with_suffix(".tmp")
        with tmp.open("w") as f:
            json.dump(state, f)
        tmp.replace(STATE_PATH)
    except Exception as e:
        print(f"[ERROR] Failed to save state: {e}")
        try:
            with STATE_PATH.open("w") as f:
                json.dump(state, f)
        except Exception as e2:
            print(f"[ERROR] Failed direct state save: {e2}")

# ---------------------------------------------------------------------------
# Runtime helpers
# ---------------------------------------------------------------------------

def get_current_state(now=None):
    with STATE_LOCK:
        state = load_state()
        return calculate_current_state(state, now=now)


def refresh_population_baseline(force=False, now=None):
    now = now or utc_now()
    with STATE_LOCK:
        state = load_state()
        last_sync = parse_timestamp(state.get("last_sync_timestamp", state["baseline_timestamp"]))
        refresh_pending = bool(state.get("refresh_pending", False) or state.get("source") == "migrated")
        if not force and not refresh_pending and (now - last_sync).total_seconds() < SYNC_INTERVAL_SECONDS:
            return False

        current_state = calculate_current_state(state, now=now)
        population, source = get_population_cached()
        if not population:
            return False

        state["baseline_population"] = int(population)
        state["baseline_timestamp"] = isoformat_z(now)
        state["last_sync_timestamp"] = isoformat_z(now)
        state["source"] = source
        state["refresh_pending"] = False
        state["continents"] = reanchor_continent_shares(state, current_state)
        save_state(state)
        return True


def updater_loop():
    while True:
        try:
            refresh_population_baseline()
        except Exception as e:
            print(f"[ERROR] Updater refresh failed: {e}")
        time.sleep(min(SYNC_INTERVAL_SECONDS, 30))


def start_updater():
    t = threading.Thread(target=updater_loop, daemon=True)
    t.start()


def current_population_and_today():
    state = get_current_state()
    return (
        int(state["population"]),
        int(state["births_today"]),
        int(state["deaths_today"]),
        state["last_updated"],
    )

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as humanity_app


class PopulationModelTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp_dir.name) / "state.json"
        self.state_patch = patch.object(humanity_app, "STATE_PATH", self.state_path)
        self.state_patch.start()
        humanity_app._CACHE.update({"anchor": None, "year": None, "ts": 0.0})
        humanity_app._pop_module.UPDATER_THREAD = None

    def tearDown(self):
        self.state_patch.stop()
        self.temp_dir.cleanup()

    def write_state(self, payload):
        self.state_path.write_text(json.dumps(payload), encoding="utf-8")

    def fixed_time(self, value):
        return humanity_app.parse_timestamp(value)

    def test_build_initial_state_creates_normalized_share_model(self):
        state = humanity_app.build_initial_state(
            now=self.fixed_time("2026-03-30T00:00:00Z"),
            baseline_population=8_000_000_000,
            source="test",
            anchor_year=2026,
            baseline_timestamp="2026-03-30T00:00:00Z",
        )

        self.assertEqual(state["version"], humanity_app.STATE_SCHEMA_VERSION)
        self.assertEqual(state["last_anchor_year"], 2026)
        self.assertEqual(state["births_per_second"], humanity_app.BIRTHS_PER_SEC)
        self.assertEqual(state["deaths_per_second"], humanity_app.DEATHS_PER_SEC)
        self.assertAlmostEqual(sum(c["baseline_share"] for c in state["continents"].values()), 1.0)
        self.assertAlmostEqual(sum(c["birth_share"] for c in state["continents"].values()), 1.0)
        self.assertAlmostEqual(sum(c["death_share"] for c in state["continents"].values()), 1.0)
        self.assertNotIn("baseline_population", state["continents"]["Africa"])

    def test_calculate_current_state_uses_elapsed_time_without_drift_and_reconciles_continents(self):
        baseline_time = humanity_app.parse_timestamp("2026-03-30T00:00:00Z")
        state = humanity_app.build_initial_state(
            now=baseline_time,
            baseline_population=8_000_000_000,
            source="test",
            baseline_timestamp="2026-03-30T00:00:00Z",
        )

        after_ten_seconds = humanity_app.calculate_current_state(
            state,
            now=humanity_app.parse_timestamp("2026-03-30T00:00:10Z"),
        )
        after_twenty_seconds = humanity_app.calculate_current_state(
            state,
            now=humanity_app.parse_timestamp("2026-03-30T00:00:20Z"),
        )
        serialized = humanity_app.serialize_current_state(after_twenty_seconds)

        self.assertEqual(int(after_ten_seconds["population"]), 8_000_000_025)
        self.assertEqual(int(after_twenty_seconds["population"]), 8_000_000_050)
        self.assertEqual(int(after_twenty_seconds["population"] - after_ten_seconds["population"]), 25)
        self.assertEqual(sum(c["population"] for c in serialized["continents"].values()), serialized["population"])
        self.assertEqual(sum(c["births_today"] for c in serialized["continents"].values()), serialized["births_today"])
        self.assertEqual(sum(c["deaths_today"] for c in serialized["continents"].values()), serialized["deaths_today"])

    def test_calculate_current_state_derives_today_counters_from_timestamp(self):
        baseline_time = humanity_app.parse_timestamp("2026-03-30T00:00:00Z")
        state = humanity_app.build_initial_state(
            now=baseline_time,
            baseline_population=8_000_000_000,
            source="test",
            baseline_timestamp="2026-03-30T00:00:00Z",
        )

        noon_state = humanity_app.calculate_current_state(
            state,
            now=humanity_app.parse_timestamp("2026-03-30T12:00:00Z"),
        )

        self.assertEqual(int(noon_state["births_today"]), int(humanity_app.BIRTHS_PER_SEC * 43200))
        self.assertEqual(int(noon_state["deaths_today"]), int(humanity_app.DEATHS_PER_SEC * 43200))

    def test_load_state_migrates_legacy_runtime_snapshot(self):
        self.write_state(
            {
                "population": 8123457099.0,
                "births_today": 533.2,
                "deaths_today": 223.2,
                "last_midnight": "2025-09-23",
                "last_updated": "2025-09-23T03:43:45Z",
                "continents": {
                    name: {"population": data["population"]}
                    for name, data in humanity_app.BASE_CONTINENTS.items()
                },
            }
        )

        state = humanity_app.load_state()

        self.assertEqual(state["version"], humanity_app.STATE_SCHEMA_VERSION)
        self.assertIn("baseline_population", state)
        self.assertIn("baseline_timestamp", state)
        self.assertEqual(state["source"], "migrated")
        self.assertIn("last_anchor_year", state)
        self.assertEqual(set(state["continents"].keys()), set(humanity_app.BASE_CONTINENTS.keys()))
        self.assertAlmostEqual(sum(c["baseline_share"] for c in state["continents"].values()), 1.0)
        self.assertAlmostEqual(sum(c["birth_share"] for c in state["continents"].values()), 1.0)
        self.assertAlmostEqual(sum(c["death_share"] for c in state["continents"].values()), 1.0)
        self.assertNotIn("baseline_population", state["continents"]["Africa"])

    def test_migrated_state_reanchors_with_authoritative_yearly_data(self):
        self.write_state(
            {
                "population": 8123457099.0,
                "last_updated": "2026-03-30T00:00:00Z",
                "continents": {
                    name: {"population": data["population"]}
                    for name, data in humanity_app.BASE_CONTINENTS.items()
                },
            }
        )
        migrated_state = humanity_app.load_state()
        self.assertEqual(migrated_state["source"], "migrated")

        anchor_bundle = {
            "population": 8_100_000_000,
            "births_per_second": 4.4,
            "deaths_per_second": 1.9,
            "source": "un_wpp",
            "anchor_year": 2026,
            "data_year": 2026,
        }
        with patch.object(humanity_app._pop_module, "get_authoritative_population_anchor", return_value=anchor_bundle):
            updated = humanity_app.refresh_population_baseline(
                force=False,
                now=self.fixed_time("2026-03-30T00:05:00Z"),
            )

        self.assertTrue(updated)
        refreshed_state = humanity_app.load_state()
        self.assertEqual(refreshed_state["baseline_population"], 8_100_000_000)
        self.assertEqual(refreshed_state["source"], "un_wpp")
        self.assertEqual(refreshed_state["births_per_second"], 4.4)
        self.assertEqual(refreshed_state["deaths_per_second"], 1.9)
        self.assertEqual(refreshed_state["last_anchor_year"], 2026)

    def test_refresh_without_year_change_is_a_noop(self):
        baseline_time = self.fixed_time("2026-03-30T00:00:00Z")
        self.write_state(
            humanity_app.build_initial_state(
                now=baseline_time,
                baseline_population=8_000_000_000,
                source="initial",
                anchor_year=2026,
                baseline_timestamp="2026-03-30T00:00:00Z",
            )
        )

        anchor_bundle = {
            "population": 8_100_000_000,
            "births_per_second": 4.4,
            "deaths_per_second": 1.9,
            "source": "un_wpp",
            "anchor_year": 2026,
            "data_year": 2026,
        }
        with patch.object(humanity_app._pop_module, "get_authoritative_population_anchor", return_value=anchor_bundle):
            updated = humanity_app.refresh_population_baseline(
                force=False,
                now=self.fixed_time("2026-03-30T00:05:00Z"),
            )

        self.assertFalse(updated)

    def test_refresh_reanchors_when_crossing_into_new_anchor_year(self):
        baseline_time = self.fixed_time("2026-01-01T00:00:00Z")
        self.write_state(
            humanity_app.build_initial_state(
                now=baseline_time,
                baseline_population=8_000_000_000,
                source="initial",
                anchor_year=2026,
            )
        )

        anchor_bundle = {
            "population": 8_140_000_000,
            "births_per_second": 4.1,
            "deaths_per_second": 1.7,
            "source": "world_bank",
            "anchor_year": 2027,
            "data_year": 2026,
        }
        with patch.object(humanity_app._pop_module, "get_authoritative_population_anchor", return_value=anchor_bundle):
            updated = humanity_app.refresh_population_baseline(
                force=False,
                now=self.fixed_time("2027-01-01T00:00:05Z"),
            )

        self.assertTrue(updated)
        refreshed_state = humanity_app.load_state()
        self.assertEqual(refreshed_state["baseline_population"], 8_140_000_000)
        self.assertEqual(refreshed_state["source"], "world_bank")
        self.assertEqual(refreshed_state["last_anchor_year"], 2027)
        self.assertEqual(refreshed_state["baseline_timestamp"], "2027-01-01T00:00:00Z")

    def test_refresh_keeps_existing_state_when_authorities_fail(self):
        baseline_time = self.fixed_time("2026-01-01T00:00:00Z")
        self.write_state(
            humanity_app.build_initial_state(
                now=baseline_time,
                baseline_population=8_000_000_000,
                source="initial",
                anchor_year=2026,
            )
        )

        with patch.object(humanity_app._pop_module, "get_authoritative_population_anchor", return_value=None):
            updated = humanity_app.refresh_population_baseline(
                force=False,
                now=self.fixed_time("2027-01-01T00:00:05Z"),
            )

        self.assertFalse(updated)
        preserved_state = humanity_app.load_state()
        self.assertEqual(preserved_state["baseline_population"], 8_000_000_000)
        self.assertEqual(preserved_state["last_anchor_year"], 2026)

    def test_live_state_route_returns_authoritative_anchor_contract(self):
        baseline_time = humanity_app.parse_timestamp("2026-03-30T00:00:00Z")
        self.write_state(
            humanity_app.build_initial_state(
                now=baseline_time,
                baseline_population=8_000_000_000,
                source="test",
                anchor_year=2026,
                baseline_timestamp="2026-03-30T00:00:00Z",
            )
        )

        with humanity_app.app.test_client() as client:
            with patch.object(humanity_app._pop_module, "utc_now", return_value=humanity_app.parse_timestamp("2026-03-30T00:01:00Z")):
                live_response = client.get("/api/live-state")

        self.assertEqual(live_response.status_code, 200)
        live_payload = live_response.get_json()
        self.assertEqual(
            set(live_payload.keys()),
            {"baselinePopulation", "baselineTimestamp", "birthsPerSecond", "deathsPerSecond", "serverTimestamp", "source", "lastAnchorYear"}
        )
        self.assertEqual(live_payload["baselinePopulation"], 8_000_000_000)
        self.assertEqual(live_payload["baselineTimestamp"], "2026-03-30T00:00:00Z")
        self.assertEqual(live_payload["birthsPerSecond"], humanity_app.BIRTHS_PER_SEC)
        self.assertEqual(live_payload["deathsPerSecond"], humanity_app.DEATHS_PER_SEC)
        self.assertEqual(live_payload["serverTimestamp"], "2026-03-30T00:01:00Z")
        self.assertEqual(live_payload["source"], "test")
        self.assertEqual(live_payload["lastAnchorYear"], 2026)
        self.assertNotIn("population", live_payload)
        self.assertNotIn("births_today", live_payload)
        self.assertNotIn("deaths_today", live_payload)

    def test_restart_behavior_preserves_deterministic_state(self):
        baseline_time = self.fixed_time("2026-03-30T00:00:00Z")
        self.write_state(
            humanity_app.build_initial_state(
                now=baseline_time,
                baseline_population=8_000_000_000,
                source="initial",
                anchor_year=2026,
                baseline_timestamp="2026-03-30T00:00:00Z",
            )
        )

        check_time = self.fixed_time("2026-03-30T00:10:00Z")
        before_restart = humanity_app.serialize_current_state(
            humanity_app.calculate_current_state(humanity_app.load_state(), now=check_time)
        )
        humanity_app._CACHE.update({"anchor": None, "year": None, "ts": 0.0})
        after_restart = humanity_app.serialize_current_state(
            humanity_app.calculate_current_state(humanity_app.load_state(), now=check_time)
        )
        self.assertEqual(before_restart, after_restart)

    def test_manual_reanchor_updates_baseline_not_runtime_counter(self):
        baseline_time = humanity_app.parse_timestamp("2026-03-30T00:00:00Z")
        self.write_state(
            humanity_app.build_initial_state(
                now=baseline_time,
                baseline_population=8_000_000_000,
                source="initial",
                anchor_year=2026,
                baseline_timestamp="2026-03-30T00:00:00Z",
            )
        )

        refresh_time = humanity_app.parse_timestamp("2026-03-30T01:00:00Z")
        anchor_bundle = {
            "population": 8_100_000_000,
            "births_per_second": 4.4,
            "deaths_per_second": 1.9,
            "source": "un_wpp",
            "anchor_year": 2026,
            "data_year": 2026,
        }
        with patch.object(humanity_app._pop_module, "get_authoritative_population_anchor", return_value=anchor_bundle):
            updated = humanity_app.refresh_population_baseline(force=True, now=refresh_time, target_year=2026)

        self.assertTrue(updated)
        stored_state = humanity_app.load_state()
        self.assertEqual(stored_state["baseline_population"], 8_100_000_000)
        self.assertEqual(stored_state["baseline_timestamp"], "2026-01-01T00:00:00Z")
        self.assertEqual(stored_state["births_per_second"], 4.4)
        self.assertEqual(stored_state["deaths_per_second"], 1.9)
        self.assertEqual(stored_state["source"], "un_wpp")
        self.assertEqual(stored_state["last_anchor_year"], 2026)

    def test_bootstrap_population_system_starts_updater_when_enabled(self):
        with patch.object(humanity_app, "UPDATER_ENABLED", True), patch.object(humanity_app, "start_updater", return_value=True) as start_mock:
            started = humanity_app.bootstrap_population_system()

        self.assertTrue(started)
        start_mock.assert_called_once_with()

    def test_bootstrap_population_system_skips_when_disabled(self):
        with patch.object(humanity_app, "UPDATER_ENABLED", False), patch.object(humanity_app, "start_updater") as start_mock:
            started = humanity_app.bootstrap_population_system()

        self.assertFalse(started)
        start_mock.assert_not_called()

    def test_live_state_route_allows_sustained_polling_before_burst_limit(self):
        baseline_time = self.fixed_time("2026-03-30T00:00:00Z")
        self.write_state(
            humanity_app.build_initial_state(
                now=baseline_time,
                baseline_population=8_000_000_000,
                source="test",
                anchor_year=2026,
                baseline_timestamp="2026-03-30T00:00:00Z",
            )
        )

        with humanity_app.app.test_client() as client:
            responses = []
            for _ in range(120):
                responses.append(client.get("/api/live-state", environ_overrides={"REMOTE_ADDR": "10.0.0.99"}).status_code)
            limited = client.get("/api/live-state", environ_overrides={"REMOTE_ADDR": "10.0.0.99"})

        self.assertTrue(all(status == 200 for status in responses))
        self.assertEqual(limited.status_code, 429)

    def test_admin_reanchor_requires_valid_token(self):
        anchor_bundle = {
            "population": 8_100_000_000,
            "births_per_second": 4.4,
            "deaths_per_second": 1.9,
            "source": "un_wpp",
            "anchor_year": 2026,
            "data_year": 2026,
        }
        with humanity_app.app.test_client() as client, patch.object(humanity_app, "ADMIN_REANCHOR_TOKEN", "secret-token"), patch.object(humanity_app._pop_module, "get_authoritative_population_anchor", return_value=anchor_bundle):
            forbidden = client.post("/admin/reanchor")
            allowed = client.post(
                "/admin/reanchor",
                headers={"X-Admin-Token": "secret-token"},
                json={},
            )

        self.assertEqual(forbidden.status_code, 403)
        self.assertNotEqual(allowed.status_code, 403)


if __name__ == "__main__":
    unittest.main()
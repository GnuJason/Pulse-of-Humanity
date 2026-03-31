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
        humanity_app._CACHE.update({"population": None, "source": None, "ts": 0.0})

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
        )

        self.assertEqual(state["version"], humanity_app.STATE_SCHEMA_VERSION)
        self.assertFalse(state["refresh_pending"])
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
        self.assertTrue(state["refresh_pending"])
        self.assertEqual(set(state["continents"].keys()), set(humanity_app.BASE_CONTINENTS.keys()))
        self.assertAlmostEqual(sum(c["baseline_share"] for c in state["continents"].values()), 1.0)
        self.assertAlmostEqual(sum(c["birth_share"] for c in state["continents"].values()), 1.0)
        self.assertAlmostEqual(sum(c["death_share"] for c in state["continents"].values()), 1.0)
        self.assertNotIn("baseline_population", state["continents"]["Africa"])

    def test_refresh_pending_state_bypasses_sync_interval_once(self):
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
        self.assertTrue(migrated_state["refresh_pending"])

        with patch.object(humanity_app, "get_population_cached", return_value=(8_100_000_000, "api_ninjas")):
            updated = humanity_app.refresh_population_baseline(
                force=False,
                now=self.fixed_time("2026-03-30T00:05:00Z"),
            )

        self.assertTrue(updated)
        refreshed_state = humanity_app.load_state()
        self.assertEqual(refreshed_state["baseline_population"], 8_100_000_000)
        self.assertEqual(refreshed_state["source"], "api_ninjas")
        self.assertFalse(refreshed_state["refresh_pending"])

    def test_refresh_without_pending_respects_sync_interval(self):
        baseline_time = self.fixed_time("2026-03-30T00:00:00Z")
        self.write_state(
            humanity_app.build_initial_state(
                now=baseline_time,
                baseline_population=8_000_000_000,
                source="initial",
            )
        )

        with patch.object(humanity_app, "get_population_cached", return_value=(8_100_000_000, "api_ninjas")):
            updated = humanity_app.refresh_population_baseline(
                force=False,
                now=self.fixed_time("2026-03-30T00:05:00Z"),
            )

        self.assertFalse(updated)

    def test_live_state_and_population_endpoint_are_consistent(self):
        baseline_time = humanity_app.parse_timestamp("2026-03-30T00:00:00Z")
        self.write_state(
            humanity_app.build_initial_state(
                now=baseline_time,
                baseline_population=8_000_000_000,
                source="test",
            )
        )

        with humanity_app.app.test_client() as client:
            with patch.object(humanity_app, "utc_now", return_value=humanity_app.parse_timestamp("2026-03-30T00:01:00Z")):
                live_response = client.get("/api/live-state")
                population_response = client.get("/population")

        self.assertEqual(live_response.status_code, 200)
        self.assertEqual(population_response.status_code, 200)
        live_payload = live_response.get_json()
        population_payload = population_response.get_json()
        self.assertEqual(live_payload["population"], population_payload["population"])
        self.assertEqual(live_payload["last_updated"], population_payload["last_updated"])
        self.assertEqual(sum(c["population"] for c in live_payload["continents"].values()), live_payload["population"])

    def test_restart_behavior_preserves_deterministic_state(self):
        baseline_time = self.fixed_time("2026-03-30T00:00:00Z")
        self.write_state(
            humanity_app.build_initial_state(
                now=baseline_time,
                baseline_population=8_000_000_000,
                source="initial",
            )
        )

        check_time = self.fixed_time("2026-03-30T00:10:00Z")
        before_restart = humanity_app.serialize_current_state(
            humanity_app.calculate_current_state(humanity_app.load_state(), now=check_time)
        )
        humanity_app._CACHE.update({"population": None, "source": None, "ts": 0.0})
        after_restart = humanity_app.serialize_current_state(
            humanity_app.calculate_current_state(humanity_app.load_state(), now=check_time)
        )
        self.assertEqual(before_restart, after_restart)

    def test_refresh_population_baseline_updates_baseline_not_runtime_counter(self):
        baseline_time = humanity_app.parse_timestamp("2026-03-30T00:00:00Z")
        self.write_state(
            humanity_app.build_initial_state(
                now=baseline_time,
                baseline_population=8_000_000_000,
                source="initial",
            )
        )

        refresh_time = humanity_app.parse_timestamp("2026-03-30T01:00:00Z")
        with patch.object(humanity_app, "get_population_cached", return_value=(8_100_000_000, "api_ninjas")):
            updated = humanity_app.refresh_population_baseline(force=True, now=refresh_time)

        self.assertTrue(updated)
        stored_state = humanity_app.load_state()
        self.assertEqual(stored_state["baseline_population"], 8_100_000_000)
        self.assertEqual(stored_state["baseline_timestamp"], "2026-03-30T01:00:00Z")
        self.assertEqual(stored_state["source"], "api_ninjas")
        self.assertFalse(stored_state["refresh_pending"])

    def test_live_state_route_allows_sustained_polling_before_burst_limit(self):
        baseline_time = self.fixed_time("2026-03-30T00:00:00Z")
        self.write_state(
            humanity_app.build_initial_state(
                now=baseline_time,
                baseline_population=8_000_000_000,
                source="test",
            )
        )

        with humanity_app.app.test_client() as client:
            responses = []
            for _ in range(120):
                responses.append(client.get("/api/live-state", environ_overrides={"REMOTE_ADDR": "10.0.0.99"}).status_code)
            limited = client.get("/api/live-state", environ_overrides={"REMOTE_ADDR": "10.0.0.99"})

        self.assertTrue(all(status == 200 for status in responses))
        self.assertEqual(limited.status_code, 429)


if __name__ == "__main__":
    unittest.main()
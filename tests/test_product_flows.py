import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = {
    "wf01": ROOT / "n8n/workflows/registration/WF_01_USER_REGISTRATION_MAN_WOMAN_DEV.json",
    "wf03": ROOT / "n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.json",
    "wf05": ROOT / "n8n/workflows/catalog/WF_05_PROFILE_CATALOG_RANKING_DEV.json",
}


def load_workflow(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_score(matches):
    considered = sum(1 for configured, _matched in matches if configured)
    matched = sum(1 for configured, is_match in matches if configured and is_match)
    return matched, considered, 0 if considered == 0 else matched / considered


def normalize_city(value):
    return re.sub(r"\s+", " ", value.strip().lower().replace("ё", "е"))


class WorkflowStaticTests(unittest.TestCase):
    def test_dev_workflows_are_valid_inactive_json(self):
        for name, path in WORKFLOWS.items():
            with self.subTest(name=name):
                workflow = load_workflow(path)
                self.assertFalse(workflow["active"])
                self.assertTrue(workflow.get("meta", {}).get("devOnly"))

    def test_node_names_ids_references_and_connections(self):
        reference_pattern = re.compile(r"\$\((?:'([^']+)'|\"([^\"]+)\")\)")
        for name, path in WORKFLOWS.items():
            with self.subTest(name=name):
                workflow = load_workflow(path)
                names = [node["name"] for node in workflow["nodes"]]
                ids = [node["id"] for node in workflow["nodes"]]
                self.assertEqual(len(names), len(set(names)))
                self.assertEqual(len(ids), len(set(ids)))
                known = set(names)
                reachable = {names[0]}
                for node in workflow["nodes"]:
                    payload = json.dumps(node.get("parameters", {}), ensure_ascii=False)
                    for match in reference_pattern.finditer(payload):
                        reference = match.group(1) or match.group(2)
                        self.assertIn(reference, known, f"{node['name']} -> {reference}")
                for source, streams in workflow.get("connections", {}).items():
                    self.assertIn(source, known)
                    for outputs in streams.values():
                        for branch in outputs:
                            for edge in branch:
                                self.assertIn(edge["node"], known)
                changed = True
                while changed:
                    changed = False
                    for source, streams in workflow.get("connections", {}).items():
                        if source not in reachable:
                            continue
                        for outputs in streams.values():
                            for branch in outputs:
                                for edge in branch:
                                    if edge["node"] not in reachable:
                                        reachable.add(edge["node"])
                                        changed = True
                self.assertEqual(reachable, known, f"unreachable nodes: {known - reachable}")

    def test_postgres_v26_nodes_use_official_query_replacement_json_bind(self):
        for name, path in WORKFLOWS.items():
            workflow = load_workflow(path)
            for node in workflow["nodes"]:
                if node["type"] != "n8n-nodes-base.postgres":
                    continue
                query = node["parameters"].get("query", "")
                placeholders = [int(value) for value in re.findall(r"\$([1-9][0-9]*)", query)]
                with self.subTest(workflow=name, node=node["name"]):
                    self.assertEqual(node["typeVersion"], 2.6)
                    self.assertNotIn("{{", query)
                    self.assertEqual(set(placeholders), {1})
                    self.assertIn("$1::jsonb", query)
                    self.assertNotIn("queryParams", node["parameters"].get("additionalFields", {}))
                    replacement = node["parameters"].get("options", {}).get("queryReplacement")
                    self.assertIsInstance(replacement, str)
                    self.assertTrue(replacement.startswith("={{JSON.stringify({"))

    def test_completed_woman_lifecycle_contract_is_explicit(self):
        workflow = load_workflow(WORKFLOWS["wf01"])
        reload_query = next(node for node in workflow["nodes"] if node["name"] == "Reload Role State")["parameters"]["query"]
        reply_code = next(node for node in workflow["nodes"] if node["name"] == "Prepare Role-Specific Reply")["parameters"]["jsCode"]
        handoff = next(node for node in workflow["nodes"] if node["name"] == "Should Handoff WOMAN Event")
        for state in ("IN_PROGRESS", "PENDING_MODERATION", "ACTIVE", "BLOCKED"):
            self.assertIn(state, reload_query)
        self.assertIn("Анкета заполнена и ожидает модерации.", reply_code)
        self.assertIn("woman_state === 'IN_PROGRESS'", json.dumps(handoff, ensure_ascii=False))

    def test_woman_flow_uses_tz02_fields_and_real_ai_call(self):
        raw = WORKFLOWS["wf03"].read_text(encoding="utf-8")
        for field in (
            "name", "age", "city", "district", "height_cm", "weight_kg",
            "breast_size", "description", "profile_prices", "profile_meeting_places",
        ):
            self.assertIn(field, raw)
        for obsolete in ("communication_style", "hobbies", "education"):
            self.assertNotIn(obsolete, raw)
        workflow = load_workflow(WORKFLOWS["wf03"])
        self.assertTrue(any(node["name"] == "DeepSeek Structured Extraction" for node in workflow["nodes"]))

    def test_man_flow_has_confirmation_and_no_generic_questionnaire(self):
        raw = WORKFLOWS["wf01"].read_text(encoding="utf-8")
        for expected in (
            "man_name:keep", "man_name:change", "male_search_context",
            "normalize_city_name", "AWAITING_NAME_CONFIRMATION",
            "AWAITING_MANUAL_NAME", "AWAITING_CITY", "WF_03_TRIGGER_URL",
            "Register or Resolve Telegram User", "role_decision",
        ):
            self.assertIn(expected, raw)
        for obsolete in ("communication_style", "hobbies", "education"):
            self.assertNotIn(obsolete, raw)

    def test_start_role_and_woman_handoff_contracts(self):
        workflow = load_workflow(WORKFLOWS["wf01"])
        normalize = next(node for node in workflow["nodes"] if node["name"] == "Normalize Telegram Event")
        self.assertIn("action='START'", normalize["parameters"]["jsCode"])
        self.assertIn("UNKNOWN_COMMAND", normalize["parameters"]["jsCode"])
        state = next(node for node in workflow["nodes"] if node["name"] == "Apply Role and Onboarding Event")
        query = state["parameters"]["query"]
        self.assertIn("role IS NULL", query)
        self.assertIn("'REJECTED'", query)
        self.assertIn("pg_advisory_xact_lock", query)
        handoff = next(node for node in workflow["nodes"] if node["name"] == "Handoff WOMAN Event to WF_03")
        for key in ("telegram_id", "chat_id", "update_type", "message_text", "photo_file_id", "user_id", "profile_id", "session_id"):
            self.assertIn(key, handoff["parameters"]["body"])

    def test_wf03_unavailable_session_has_controlled_terminal_path(self):
        workflow = load_workflow(WORKFLOWS["wf03"])
        nodes = {node["name"]: node for node in workflow["nodes"]}
        load = nodes["Load WOMAN Draft Session"]
        query = load["parameters"]["query"]
        self.assertIn("LEFT JOIN chosen ON true", query)
        self.assertIn("WOMAN_SESSION_NOT_AVAILABLE", query)
        self.assertIn("session_available", query)
        self.assertIn("WOMAN Session Available", nodes)
        branches = workflow["connections"]["WOMAN Session Available"]["main"]
        self.assertEqual(branches[0][0]["node"], "Is Photo")
        self.assertEqual(branches[1][0]["node"], "Respond WOMAN Flow")

    def test_external_calls_have_timeout_and_controlled_error_routes(self):
        wf01 = load_workflow(WORKFLOWS["wf01"])
        wf03 = load_workflow(WORKFLOWS["wf03"])
        handoff = next(node for node in wf01["nodes"] if node["name"] == "Handoff WOMAN Event to WF_03")
        self.assertGreater(handoff["parameters"]["options"]["timeout"], 0)
        self.assertEqual(handoff["onError"], "continueErrorOutput")
        self.assertTrue(handoff["parameters"]["options"]["response"]["response"]["neverError"])
        self.assertEqual(
            wf01["connections"][handoff["name"]]["main"][1][0]["node"],
            "Prepare WF_03 Failure Reply",
        )
        failure = next(node for node in wf01["nodes"] if node["name"] == "Prepare WF_03 Failure Reply")
        self.assertIn("Не удалось обработать ответ. Попробуйте ещё раз.", failure["parameters"]["jsCode"])
        deepseek = next(node for node in wf03["nodes"] if node["name"] == "DeepSeek Structured Extraction")
        validate = next(node for node in wf03["nodes"] if node["name"] == "Validate AI Extraction")
        self.assertGreater(deepseek["parameters"]["options"]["timeout"], 0)
        self.assertEqual(deepseek["onError"], "continueErrorOutput")
        self.assertEqual(validate["onError"], "continueErrorOutput")
        for source in (deepseek["name"], validate["name"]):
            self.assertEqual(
                wf03["connections"][source]["main"][1][0]["node"],
                "Prepare WOMAN Processing Error",
            )

    def test_wf03_dev_webhook_uses_header_auth_credential_contract(self):
        wf01 = load_workflow(WORKFLOWS["wf01"])
        wf03 = load_workflow(WORKFLOWS["wf03"])
        webhook = next(node for node in wf03["nodes"] if node["name"] == "WOMAN Profile Webhook")
        handoff = next(node for node in wf01["nodes"] if node["name"] == "Handoff WOMAN Event to WF_03")
        self.assertEqual(webhook["parameters"]["authentication"], "headerAuth")
        self.assertEqual(handoff["parameters"]["authentication"], "genericCredentialType")
        self.assertEqual(handoff["parameters"]["genericAuthType"], "httpHeaderAuth")
        self.assertEqual(webhook["credentials"]["httpHeaderAuth"], handoff["credentials"]["httpHeaderAuth"])
        self.assertIn("PLACEHOLDER", webhook["credentials"]["httpHeaderAuth"]["id"])

    def test_terminal_woman_profiles_precede_stale_drafts(self):
        workflow = load_workflow(WORKFLOWS["wf01"])
        apply_query = next(node for node in workflow["nodes"] if node["name"] == "Apply Role and Onboarding Event")["parameters"]["query"]
        reload_query = next(node for node in workflow["nodes"] if node["name"] == "Reload Role State")["parameters"]["query"]
        self.assertIn("terminal_woman_profile", apply_query)
        self.assertIn("NOT EXISTS(SELECT 1 FROM terminal_woman_profile)", apply_query)
        active = reload_query.index("WHEN 'ACTIVE' THEN 0")
        pending = reload_query.index("WHEN 'PENDING_MODERATION' THEN 1")
        blocked = reload_query.index("WHEN 'BLOCKED' THEN 2")
        draft = reload_query.index("WHEN 'DRAFT' THEN 3")
        self.assertLess(active, pending)
        self.assertLess(pending, blocked)
        self.assertLess(blocked, draft)

    def test_finalize_requires_draft_profile_and_in_progress_session(self):
        workflow = load_workflow(WORKFLOWS["wf03"])
        query = next(node for node in workflow["nodes"] if node["name"] == "Finalize WOMAN Profile")["parameters"]["query"]
        self.assertIn("s.status='IN_PROGRESS'", query)
        self.assertIn("p.status='DRAFT'", query)
        self.assertIn("WOMAN_FINALIZATION_NOT_AVAILABLE", query)

    def test_woman_collection_and_photo_persistence_is_explicit(self):
        workflow = load_workflow(WORKFLOWS["wf03"])
        persist = next(node for node in workflow["nodes"] if node["name"] == "Persist WOMAN Extraction")
        query = persist["parameters"]["query"]
        for operation in ("APPEND", "UPDATE", "DELETE"):
            self.assertIn(operation, query)
        self.assertNotIn("ON CONFLICT(profile_id,position) DO UPDATE", query)
        photo = next(node for node in workflow["nodes"] if node["name"] == "Save WOMAN Photo")
        self.assertIn("pg_advisory_xact_lock", photo["parameters"]["query"])
        self.assertIn("telegram_file_id", photo["parameters"]["query"])


class SchemaAndRankingTests(unittest.TestCase):
    def test_city_normalization_contract(self):
        self.assertEqual(normalize_city("  Орёл  "), "орел")
        self.assertEqual(normalize_city("Нижний   Новгород"), "нижний новгород")

    def test_woman_and_man_migration_contracts(self):
        woman = (ROOT / "database/migrations/009_woman_profile_tz02_schema.sql").read_text(encoding="utf-8")
        man = (ROOT / "database/migrations/010_man_search_context_preferences_schema.sql").read_text(encoding="utf-8")
        for token in ("city_normalized", "district", "height_cm", "weight_kg", "breast_size", "profile_prices", "profile_meeting_places"):
            self.assertIn(token, woman)
        for token in (
            "male_search_context", "male_search_preferences", "onboarding_state",
            "AWAITING_NAME_CONFIRMATION", "AWAITING_MANUAL_NAME",
            "AWAITING_CITY", "TELEGRAM_CONFIRMED",
        ):
            self.assertIn(token, man)

    def test_ranking_candidate_where_has_only_product_hard_filters(self):
        sql = (ROOT / "database/queries/man_catalog_ranking_prototype.sql").read_text(encoding="utf-8")
        candidate_where = sql.split("candidates AS (", 1)[1].split("),\nscored AS", 1)[0]
        self.assertIn("p.status = 'ACTIVE'", candidate_where)
        self.assertIn("lower(owner.role) = 'woman'", candidate_where)
        self.assertIn("p.city_normalized = viewer.city_normalized", candidate_where)
        for optional in ("age_from", "districts", "height_from", "weight_from", "breast_size_from", "price_from", "meeting_place_types"):
            self.assertNotIn(optional, candidate_where)

    def test_normalized_score_ignores_unconfigured_preferences(self):
        self.assertEqual(normalized_score([]), (0, 0, 0))
        self.assertEqual(normalized_score([(True, True), (True, True)]), (2, 2, 1))
        self.assertEqual(normalized_score([(True, True), (True, False), (False, False)]), (1, 2, 0.5))
        self.assertEqual(normalized_score([(True, True), (False, False), (False, True)]), (1, 1, 1))


if __name__ == "__main__":
    unittest.main()

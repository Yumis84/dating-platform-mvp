#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / ".runtime" / "n8n-gate"
WORKFLOW_OUT = OUT / "workflows"
WORKFLOW_OUT.mkdir(parents=True, exist_ok=True)

PG_CRED_ID = "rtgPgCred0000001"
PG_CRED_NAME = "DP_RUNTIME_GATE_POSTGRES"
HEADER_CRED_ID = "rtgHdrCred000001"
HEADER_CRED_NAME = "DP_RUNTIME_GATE_WF03_HEADER"

WF_IDS = {
    "probe": "rtgBindProbe0001",
    "wf01": "rtgWf01Gate00001",
    "wf03": "rtgWf03Gate00001",
    "wf05": "rtgWf05Gate00001",
}
WEBHOOK_IDS = {
    "probe": "11111111-1111-4111-8111-111111111111",
    "wf01": "22222222-2222-4222-8222-222222222222",
    "wf03": "33333333-3333-4333-8333-333333333333",
    "wf05": "55555555-5555-4555-8555-555555555555",
}
CANONICAL_PATHS = {
    "wf01": "n8n/workflows/registration/WF_01_USER_REGISTRATION_MAN_WOMAN_DEV.json",
    "wf03": "n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.json",
    "wf05": "n8n/workflows/catalog/WF_05_PROFILE_CATALOG_RANKING_DEV.json",
}


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def digest(relative: str):
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def save(name: str, payload):
    path = WORKFLOW_OUT / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def bind_postgres_credentials(workflow):
    for node in workflow["nodes"]:
        if node.get("type") == "n8n-nodes-base.postgres":
            node["credentials"] = {
                "postgres": {"id": PG_CRED_ID, "name": PG_CRED_NAME}
            }


def bind_header_credential(node):
    node.setdefault("credentials", {})["httpHeaderAuth"] = {
        "id": HEADER_CRED_ID,
        "name": HEADER_CRED_NAME,
    }


def assert_if_v2_contract(workflow, workflow_name):
    checked = []
    for node in workflow["nodes"]:
        if node.get("type") != "n8n-nodes-base.if":
            continue
        if node.get("typeVersion") != 2:
            raise RuntimeError(f"{workflow_name}/{node['name']}: expected IF typeVersion 2")
        contract = node.get("parameters", {}).get("conditions", {})
        if "boolean" in contract or "string" in contract:
            raise RuntimeError(
                f"{workflow_name}/{node['name']}: legacy conditions.boolean/string reached strict runtime gate"
            )
        conditions = contract.get("conditions")
        if not isinstance(conditions, list) or not conditions or not contract.get("combinator"):
            raise RuntimeError(
                f"{workflow_name}/{node['name']}: missing n8n v2 filter conditions/combinator contract"
            )
        for condition in conditions:
            operator = condition.get("operator") or {}
            if not condition.get("leftValue") or not operator.get("type") or not operator.get("operation"):
                raise RuntimeError(
                    f"{workflow_name}/{node['name']}: malformed n8n v2 filter condition {condition!r}"
                )
        checked.append(node["name"])
    return checked


def assert_wf01_handoff_contract(workflow):
    nodes = {node["name"]: node for node in workflow["nodes"]}
    handoff = nodes["Handoff WOMAN Event to WF_03"]
    response = handoff["parameters"]["options"]["response"]["response"]
    if response.get("responseFormat") != "autodetect":
        raise RuntimeError(
            "WF_01 canonical handoff must use responseFormat=autodetect for raw request bodies on n8n 2.34.5"
        )
    code = nodes["Prepare WF_03 Reply"]["parameters"]["jsCode"]
    for marker in ("JSON.parse", "Array.isArray", "handoff_ok"):
        if marker not in code:
            raise RuntimeError(f"WF_01 canonical reply parser is missing {marker}")


def clone_wf01():
    wf = load(CANONICAL_PATHS["wf01"])
    checked_ifs = assert_if_v2_contract(wf, "WF_01")
    assert_wf01_handoff_contract(wf)

    wf["id"] = WF_IDS["wf01"]
    wf["name"] = "WF_01_RUNTIME_GATE"
    wf["active"] = False
    wf.setdefault("meta", {})["runtimeGateOnly"] = True
    wf["meta"]["strictCanonicalIfNodes"] = checked_ifs
    wf["meta"]["canonicalSha256"] = digest(CANONICAL_PATHS["wf01"])
    node_by_name = {n["name"]: n for n in wf["nodes"]}

    # Test-only transport adapter: preserve every core state/routing/SQL/HTTP node,
    # replacing only the Telegram edge with a local POST webhook.
    trigger = node_by_name["Telegram Trigger"]
    trigger["type"] = "n8n-nodes-base.webhook"
    trigger["typeVersion"] = 2
    trigger["webhookId"] = WEBHOOK_IDS["wf01"]
    trigger.pop("credentials", None)
    trigger["parameters"] = {
        "httpMethod": "POST",
        "path": "runtime-gate/wf01",
        "responseMode": "responseNode",
        "options": {},
    }

    normalize = node_by_name["Normalize Telegram Event"]
    code = normalize["parameters"]["jsCode"]
    old = "const cb=$json.callback_query; const msg=$json.message;"
    new = "const incoming=$json.body||$json; const cb=incoming.callback_query; const msg=incoming.message;"
    if old not in code:
        raise RuntimeError("WF_01 Normalize Telegram Event source changed; refusing unsafe runtime transform")
    normalize["parameters"]["jsCode"] = code.replace(old, new, 1)

    bind_postgres_credentials(wf)
    bind_header_credential(node_by_name["Handoff WOMAN Event to WF_03"])

    for name in {
        "Send Role Choice",
        "Send MAN Name Confirmation",
        "Send MAN Catalog Choice",
        "Send Role-Specific Reply",
    }:
        node = node_by_name[name]
        node["type"] = "n8n-nodes-base.code"
        node["typeVersion"] = 2
        node.pop("credentials", None)
        node["parameters"] = {"jsCode": "return $input.all();"}

    for name in ("Answer Callback Query", "DEV Flow Complete"):
        node = node_by_name[name]
        node["type"] = "n8n-nodes-base.respondToWebhook"
        node["typeVersion"] = 1.4
        node.pop("credentials", None)
        node["parameters"] = {
            "respondWith": "json",
            "responseBody": "={{$json}}",
            "options": {},
        }

    return wf


def clone_wf03():
    wf = load(CANONICAL_PATHS["wf03"])
    checked_ifs = assert_if_v2_contract(wf, "WF_03")

    wf["id"] = WF_IDS["wf03"]
    wf["name"] = "WF_03_RUNTIME_GATE"
    wf["active"] = False
    wf.setdefault("meta", {})["runtimeGateOnly"] = True
    wf["meta"]["strictCanonicalIfNodes"] = checked_ifs
    wf["meta"]["canonicalSha256"] = digest(CANONICAL_PATHS["wf03"])
    node_by_name = {n["name"]: n for n in wf["nodes"]}

    # Only isolate endpoint identity/credentials. All WOMAN core logic is canonical.
    trigger = node_by_name["WOMAN Profile Webhook"]
    trigger["webhookId"] = WEBHOOK_IDS["wf03"]
    trigger["parameters"]["path"] = "runtime-gate/woman-profile"
    trigger["parameters"]["authentication"] = "headerAuth"
    bind_header_credential(trigger)
    bind_postgres_credentials(wf)
    return wf


def clone_wf05():
    wf = load(CANONICAL_PATHS["wf05"])
    checked_ifs = assert_if_v2_contract(wf, "WF_05")

    wf["id"] = WF_IDS["wf05"]
    wf["name"] = "WF_05_RUNTIME_GATE"
    wf["active"] = False
    wf.setdefault("meta", {})["runtimeGateOnly"] = True
    wf["meta"]["strictCanonicalIfNodes"] = checked_ifs
    wf["meta"]["canonicalSha256"] = digest(CANONICAL_PATHS["wf05"])
    node_by_name = {n["name"]: n for n in wf["nodes"]}
    node_by_name["Catalog Webhook"]["webhookId"] = WEBHOOK_IDS["wf05"]
    node_by_name["Catalog Webhook"]["parameters"]["path"] = "runtime-gate/catalog"
    bind_postgres_credentials(wf)
    return wf


def bind_probe_workflow():
    return {
        "id": WF_IDS["probe"],
        "name": "RUNTIME_GATE_PG_JSON_BIND_PROBE",
        "active": False,
        "settings": {"executionOrder": "v1"},
        "nodes": [
            {
                "id": "rtg-probe-trigger",
                "name": "Probe Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "webhookId": WEBHOOK_IDS["probe"],
                "position": [0, 0],
                "parameters": {
                    "httpMethod": "POST",
                    "path": "runtime-gate/bind-probe",
                    "responseMode": "responseNode",
                    "options": {},
                },
            },
            {
                "id": "rtg-probe-postgres",
                "name": "Probe Postgres JSON Bind",
                "type": "n8n-nodes-base.postgres",
                "typeVersion": 2.6,
                "position": [220, 0],
                "credentials": {
                    "postgres": {"id": PG_CRED_ID, "name": PG_CRED_NAME}
                },
                "parameters": {
                    "operation": "executeQuery",
                    "query": "WITH bind AS (SELECT $1::jsonb AS data) SELECT data->>'probe' AS observed, octet_length(convert_to(data->>'probe','UTF8')) AS utf8_bytes FROM bind;",
                    "options": {
                        "queryReplacement": "={{JSON.stringify({probe:$json.body.probe})}}"
                    },
                },
            },
            {
                "id": "rtg-probe-response",
                "name": "Probe Response",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1.4,
                "position": [440, 0],
                "parameters": {
                    "respondWith": "json",
                    "responseBody": "={{$json}}",
                    "options": {},
                },
            },
        ],
        "connections": {
            "Probe Webhook": {
                "main": [[{"node": "Probe Postgres JSON Bind", "type": "main", "index": 0}]]
            },
            "Probe Postgres JSON Bind": {
                "main": [[{"node": "Probe Response", "type": "main", "index": 0}]]
            },
        },
        "meta": {"runtimeGateOnly": True, "devOnly": True},
    }


def credentials_payload():
    required = [
        "RUNTIME_GATE_PG_HOST",
        "RUNTIME_GATE_PG_DATABASE",
        "RUNTIME_GATE_PG_USER",
        "RUNTIME_GATE_PG_PASSWORD",
        "RUNTIME_GATE_HEADER_VALUE",
    ]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Missing runtime-gate environment values: {', '.join(missing)}")
    return [
        {
            "id": PG_CRED_ID,
            "name": PG_CRED_NAME,
            "type": "postgres",
            "data": {
                "host": os.environ["RUNTIME_GATE_PG_HOST"],
                "database": os.environ["RUNTIME_GATE_PG_DATABASE"],
                "user": os.environ["RUNTIME_GATE_PG_USER"],
                "password": os.environ["RUNTIME_GATE_PG_PASSWORD"],
                "port": int(os.environ.get("RUNTIME_GATE_PG_PORT", "5432")),
                "ssl": "disable",
                "allowUnauthorizedCerts": False,
                "maxConnections": 20,
            },
        },
        {
            "id": HEADER_CRED_ID,
            "name": HEADER_CRED_NAME,
            "type": "httpHeaderAuth",
            "data": {
                "name": os.environ.get("RUNTIME_GATE_HEADER_NAME", "X-Runtime-Gate"),
                "value": os.environ["RUNTIME_GATE_HEADER_VALUE"],
            },
        },
    ]


def main():
    workflows = {
        "bind-probe.json": bind_probe_workflow(),
        "wf01-runtime-gate.json": clone_wf01(),
        "wf03-runtime-gate.json": clone_wf03(),
        "wf05-runtime-gate.json": clone_wf05(),
    }
    for filename, workflow in workflows.items():
        save(filename, workflow)

    (OUT / "credentials.json").write_text(
        json.dumps(credentials_payload(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "workflow_ids": WF_IDS,
                "webhook_ids": WEBHOOK_IDS,
                "canonical_sha256": {
                    key: digest(path) for key, path in CANONICAL_PATHS.items()
                },
                "postgres_credential_id": PG_CRED_ID,
                "header_credential_id": HEADER_CRED_ID,
                "workflow_files": list(workflows.keys()),
                "strict_canonical_runtime_contract": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Strict canonical runtime-contract assertions: PASS")
    print(f"Runtime-gate artifacts written to {OUT}")


if __name__ == "__main__":
    main()

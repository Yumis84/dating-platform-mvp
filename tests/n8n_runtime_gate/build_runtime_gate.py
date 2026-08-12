#!/usr/bin/env python3
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


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


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


def clone_wf01():
    wf = load("n8n/workflows/registration/WF_01_USER_REGISTRATION_MAN_WOMAN_DEV.json")
    wf["id"] = WF_IDS["wf01"]
    wf["name"] = "WF_01_RUNTIME_GATE"
    wf["active"] = False
    wf.setdefault("meta", {})["runtimeGateOnly"] = True

    node_by_name = {n["name"]: n for n in wf["nodes"]}

    trigger = node_by_name["Telegram Trigger"]
    trigger["type"] = "n8n-nodes-base.webhook"
    trigger["typeVersion"] = 2
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
    handoff = node_by_name["Handoff WOMAN Event to WF_03"]
    bind_header_credential(handoff)

    passthrough_nodes = {
        "Send Role Choice",
        "Send MAN Name Confirmation",
        "Send MAN Catalog Choice",
        "Send Role-Specific Reply",
    }
    for name in passthrough_nodes:
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
    wf = load("n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.json")
    wf["id"] = WF_IDS["wf03"]
    wf["name"] = "WF_03_RUNTIME_GATE"
    wf["active"] = False
    wf.setdefault("meta", {})["runtimeGateOnly"] = True
    node_by_name = {n["name"]: n for n in wf["nodes"]}

    trigger = node_by_name["WOMAN Profile Webhook"]
    trigger["parameters"]["path"] = "runtime-gate/woman-profile"
    trigger["parameters"]["authentication"] = "headerAuth"
    bind_header_credential(trigger)

    bind_postgres_credentials(wf)
    return wf


def clone_wf05():
    wf = load("n8n/workflows/catalog/WF_05_PROFILE_CATALOG_RANKING_DEV.json")
    wf["id"] = WF_IDS["wf05"]
    wf["name"] = "WF_05_RUNTIME_GATE"
    wf["active"] = False
    wf.setdefault("meta", {})["runtimeGateOnly"] = True
    node_by_name = {n["name"]: n for n in wf["nodes"]}
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
                "postgres_credential_id": PG_CRED_ID,
                "header_credential_id": HEADER_CRED_ID,
                "workflow_files": list(workflows.keys()),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Runtime-gate artifacts written to {OUT}")


if __name__ == "__main__":
    main()

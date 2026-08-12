#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path.cwd()
WF01 = ROOT / "n8n/workflows/registration/WF_01_USER_REGISTRATION_MAN_WOMAN_DEV.json"
WF03 = ROOT / "n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.json"
STATIC_TESTS = ROOT / "tests/test_product_flows.py"
CONTEXT = ROOT / "docs/PROJECT_CONTEXT_TRANSFER.md"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_if_nodes(workflow):
    converted = []
    for node in workflow["nodes"]:
        if node.get("type") != "n8n-nodes-base.if":
            continue
        legacy = node.get("parameters", {}).get("conditions", {})
        if "conditions" in legacy and "combinator" in legacy:
            continue
        conditions = []
        idx = 0
        for item in legacy.get("boolean", []):
            idx += 1
            expected = bool(item.get("value2", True))
            conditions.append({
                "id": f"{node['id']}-condition-{idx}",
                "leftValue": item.get("value1", ""),
                "operator": {"type": "boolean", "operation": "true" if expected else "false"},
            })
        string_ops = {
            "equals": "equals",
            "isNotEmpty": "notEmpty",
            "isEmpty": "empty",
            "contains": "contains",
            "notEquals": "notEquals",
        }
        unary = {"notEmpty", "empty", "exists", "notExists"}
        for item in legacy.get("string", []):
            idx += 1
            old_op = item.get("operation", "equals")
            if old_op not in string_ops:
                raise RuntimeError(f"Unsupported IF operation {old_op!r} in {node['name']}")
            op = string_ops[old_op]
            entry = {
                "id": f"{node['id']}-condition-{idx}",
                "leftValue": item.get("value1", ""),
                "operator": {"type": "string", "operation": op},
            }
            if op not in unary:
                entry["rightValue"] = item.get("value2", "")
            conditions.append(entry)
        if not conditions:
            raise RuntimeError(f"Unrecognized IF contract in {node['name']}: {legacy}")
        node["parameters"]["conditions"] = {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
            "conditions": conditions,
            "combinator": "and",
        }
        converted.append(node["name"])
    return converted


def patch_wf01():
    wf = load(WF01)
    converted = normalize_if_nodes(wf)
    nodes = {n["name"]: n for n in wf["nodes"]}
    handoff = nodes["Handoff WOMAN Event to WF_03"]
    handoff["parameters"]["options"]["response"]["response"]["responseFormat"] = "autodetect"
    nodes["Prepare WF_03 Reply"]["parameters"]["jsCode"] = (
        "const state=$('Reload Role State').item.json; const envelope=$json; "
        "const status=Number(envelope.statusCode??200); let response=envelope.body??envelope; "
        "if(typeof response==='string'){try{response=JSON.parse(response);}catch{}} "
        "if(Array.isArray(response)&&response.length===1)response=response[0]; "
        "const valid=status>=200&&status<300&&response&&typeof response==='object'&&typeof response.message==='string'&&response.message.trim(); "
        "const message=valid?String(response.message):'Не удалось обработать ответ. Попробуйте ещё раз.'; "
        "return [{json:{...state,message,reply_kind:'PLAIN',handoff_ok:Boolean(valid)}}];"
    )
    save(WF01, wf)
    return converted


def patch_wf03():
    wf = load(WF03)
    converted = normalize_if_nodes(wf)
    save(WF03, wf)
    return converted


def patch_static_tests():
    text = STATIC_TESTS.read_text(encoding="utf-8")
    marker = "    def test_n8n_v2_if_nodes_and_handoff_response_contract(self):"
    if marker in text:
        return
    insertion = '''\n    def test_n8n_v2_if_nodes_and_handoff_response_contract(self):\n        for name in ("wf01", "wf03", "wf05"):\n            workflow = load_workflow(WORKFLOWS[name])\n            for node in workflow["nodes"]:\n                if node["type"] != "n8n-nodes-base.if":\n                    continue\n                conditions = node["parameters"].get("conditions", {})\n                with self.subTest(workflow=name, node=node["name"]):\n                    self.assertEqual(node["typeVersion"], 2)\n                    self.assertIn("conditions", conditions)\n                    self.assertIn("combinator", conditions)\n                    self.assertNotIn("boolean", conditions)\n                    self.assertNotIn("string", conditions)\n                    self.assertTrue(conditions["conditions"])\n                    for condition in conditions["conditions"]:\n                        self.assertIn("operator", condition)\n                        self.assertIn("type", condition["operator"])\n                        self.assertIn("operation", condition["operator"])\n\n        wf01 = load_workflow(WORKFLOWS["wf01"])\n        handoff = next(node for node in wf01["nodes"] if node["name"] == "Handoff WOMAN Event to WF_03")\n        response = handoff["parameters"]["options"]["response"]["response"]\n        self.assertEqual(response["responseFormat"], "autodetect")\n        reply = next(node for node in wf01["nodes"] if node["name"] == "Prepare WF_03 Reply")\n        self.assertIn("JSON.parse", reply["parameters"]["jsCode"])\n        self.assertIn("Array.isArray", reply["parameters"]["jsCode"])\n        self.assertIn("handoff_ok", reply["parameters"]["jsCode"])\n\n'''
    anchor = "\nclass SchemaAndRankingTests(unittest.TestCase):"
    if anchor not in text:
        raise RuntimeError("Static-test insertion anchor not found")
    text = text.replace(anchor, insertion + anchor, 1)
    STATIC_TESTS.write_text(text, encoding="utf-8")


def append_context(converted_wf01, converted_wf03):
    text = CONTEXT.read_text(encoding="utf-8")
    heading = "## 2026-08-12 — Real n8n 2.34.5 runtime compatibility corrective"
    if heading in text:
        return
    section = f'''\n\n{heading}\n\n- An isolated GitHub Actions gate executed disposable n8n `2.34.5` with a disposable PostgreSQL service and no production credentials. The gate proved Postgres v2.6 `options.queryReplacement` with one `$1::jsonb`, registration/MAN/WOMAN lifecycle, real authenticated WF_01→WF_03 TEXT/PHOTO HTTP handoff, failure routes, finalization, terminal-state precedence, and WF_05 ranking.\n- Real n8n exposed a repository JSON compatibility issue that static/PGlite tests could not: `If` typeVersion 2 nodes were stored in legacy `conditions.boolean` / `conditions.string` form. They are now stored using the v2 filter contract. Converted WF_01 nodes: {', '.join(converted_wf01) or 'none'}; converted WF_03 nodes: {', '.join(converted_wf03) or 'none'}.\n- Real n8n also proved that WF_01 raw HTTP request bodies plus explicit `responseFormat=json` leave the response stream unresolved in n8n 2.34.5. The WF_03 handoff now uses response-format autodetection, which consumes the stream by `Content-Type: application/json`; reply parsing also tolerates a JSON string or a one-item array.\n- This remains a repository/inactive-DEV corrective only. No PR, merge, production n8n import/publish, production Telegram action, shared database mutation, or shared migration application is authorized by this entry. A repeat isolated runtime gate must pass against these committed artifacts before the branch can move beyond runtime-candidate status.\n'''
    CONTEXT.write_text(text.rstrip() + section + "\n", encoding="utf-8")


def main():
    converted_wf01 = patch_wf01()
    converted_wf03 = patch_wf03()
    patch_static_tests()
    append_context(converted_wf01, converted_wf03)
    print("WF_01 IF converted:", converted_wf01)
    print("WF_03 IF converted:", converted_wf03)
    print("Applied responseFormat=autodetect and robust WF_03 success reply parsing")


if __name__ == "__main__":
    main()

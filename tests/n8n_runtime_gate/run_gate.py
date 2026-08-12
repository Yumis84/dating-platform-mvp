#!/usr/bin/env python3
import json
import os
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path

import psycopg
import requests
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / ".runtime" / "n8n-gate" / "gate-report.json"
BASE = "http://127.0.0.1:5678"
WF01 = f"{BASE}/webhook/runtime-gate/wf01"
WF03 = f"{BASE}/webhook/runtime-gate/woman-profile"
WF05 = f"{BASE}/webhook/runtime-gate/catalog"
PROBE = f"{BASE}/webhook/runtime-gate/bind-probe"
HEADER_NAME = os.environ.get("RUNTIME_GATE_HEADER_NAME", "X-Runtime-Gate")
HEADER_VALUE = os.environ["RUNTIME_GATE_HEADER_VALUE"]
DEFAULT_WF03_TARGET = WF03

DB = psycopg.connect(
    host=os.environ.get("RUNTIME_GATE_PG_HOST", "127.0.0.1"),
    port=int(os.environ.get("RUNTIME_GATE_PG_PORT", "5432")),
    dbname=os.environ.get("RUNTIME_GATE_PG_DATABASE", "runtime_gate"),
    user=os.environ.get("RUNTIME_GATE_PG_USER", "runtime_gate"),
    password=os.environ["RUNTIME_GATE_PG_PASSWORD"],
    autocommit=True,
    row_factory=dict_row,
)

results = []
ctx = {}


def rows(sql, params=()):
    with DB.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def row(sql, params=()):
    data = rows(sql, params)
    return data[0] if data else None


def scalar(sql, params=()):
    item = row(sql, params)
    return next(iter(item.values())) if item else None


def post(url, payload, *, auth=False, timeout=35):
    headers = {HEADER_NAME: HEADER_VALUE} if auth else {}
    response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    try:
        body = response.json()
    except Exception:
        body = response.text
    return response.status_code, body


def assert_equal(actual, expected, message=""):
    if actual != expected:
        raise AssertionError(message or f"expected {expected!r}, got {actual!r}")


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def test(number, name, fn):
    try:
        details = fn()
        results.append({"scenario": number, "name": name, "status": "PASS", "details": details})
        print(f"PASS {number:02d} {name} — {details}", flush=True)
    except Exception as exc:
        results.append({"scenario": number, "name": name, "status": "FAIL", "details": str(exc)})
        print(f"FAIL {number:02d} {name} — {exc}", file=sys.stderr, flush=True)


def telegram_message(telegram_id, text, first_name=""):
    return {
        "message": {
            "message_id": int(telegram_id) % 100000,
            "text": text,
            "from": {
                "id": telegram_id,
                "first_name": first_name,
                "username": f"gate_{telegram_id}",
            },
            "chat": {"id": telegram_id},
        }
    }


def telegram_callback(telegram_id, data, first_name=""):
    return {
        "callback_query": {
            "id": f"cb-{telegram_id}-{data}",
            "data": data,
            "from": {
                "id": telegram_id,
                "first_name": first_name,
                "username": f"gate_{telegram_id}",
            },
            "message": {"message_id": 1, "chat": {"id": telegram_id}},
        }
    }


def telegram_photo(telegram_id, file_id, first_name=""):
    return {
        "message": {
            "message_id": int(telegram_id) % 100000,
            "photo": [{"file_id": f"{file_id}-small"}, {"file_id": file_id}],
            "from": {
                "id": telegram_id,
                "first_name": first_name,
                "username": f"gate_{telegram_id}",
            },
            "chat": {"id": telegram_id},
        }
    }


def restart_n8n(target):
    subprocess.run(
        ["bash", str(ROOT / "tests/n8n_runtime_gate/restart_n8n.sh"), target],
        cwd=ROOT,
        check=True,
    )


def woman_snapshot():
    return row(
        """
        SELECT p.name,p.age,p.city,p.district,p.height_cm,p.weight_kg,p.breast_size,p.description,
               s.current_step,s.status session_status,p.status profile_status
        FROM profiles p JOIN profile_ai_sessions s ON s.profile_id=p.id
        WHERE p.id=%s::uuid AND s.id=%s::uuid
        """,
        (ctx["woman_profile_id"], ctx["woman_session_id"]),
    )


def test_r1():
    probe = 'Кириллица, первая, вторая; "кавычки"; apostrophe \' ;\nновая строка'
    status, body = post(PROBE, {"probe": probe})
    assert_equal(status, 200)
    assert_true(isinstance(body, dict), f"probe response is not JSON object: {body!r}")
    assert_equal(body.get("observed"), probe, "n8n split/corrupted the single JSON bind")
    assert_equal(body.get("utf8_bytes"), len(probe.encode("utf-8")))
    return "Postgres v2.6 evaluated queryReplacement as one $1::jsonb value with exact UTF-8 round-trip"


def test_r2():
    tg = 990000001
    status, body = post(WF01, telegram_message(tg, "/start", "Дмитрий"))
    assert_equal(status, 200)
    account = row(
        "SELECT u.id::text user_id,u.role,ta.telegram_id FROM users u JOIN telegram_accounts ta ON ta.user_id=u.id WHERE ta.telegram_id=%s",
        (tg,),
    )
    assert_true(account is not None, "registration produced no account")
    assert_equal(account["role"], None)
    assert_equal(scalar("SELECT count(*) FROM telegram_accounts WHERE telegram_id=%s", (tg,)), 1)
    ctx["man_tg"] = tg
    ctx["man_user_id"] = account["user_id"]
    return f"user_id={account['user_id']}; one account; role=NULL"


def test_r3():
    status, _ = post(WF01, telegram_message(ctx["man_tg"], "/start payload", "Дмитрий"))
    assert_equal(status, 200)
    account = row(
        "SELECT user_id::text FROM telegram_accounts WHERE telegram_id=%s",
        (ctx["man_tg"],),
    )
    assert_equal(account["user_id"], ctx["man_user_id"])
    assert_equal(scalar("SELECT count(*) FROM telegram_accounts WHERE telegram_id=%s", (ctx["man_tg"],)), 1)
    assert_equal(
        scalar("SELECT count(*) FROM users u WHERE NOT EXISTS (SELECT 1 FROM telegram_accounts ta WHERE ta.user_id=u.id)"),
        0,
    )
    return "repeated /start returned the same user; no duplicate account and no orphan user"


def test_r4():
    status, _ = post(WF01, telegram_callback(ctx["man_tg"], "role:man", "Дмитрий"))
    assert_equal(status, 200)
    assert_equal(scalar("SELECT role FROM users WHERE id=%s::uuid", (ctx["man_user_id"],)), "man")
    assert_equal(scalar("SELECT count(*) FROM male_search_context WHERE user_id=%s::uuid", (ctx["man_user_id"],)), 1)
    status, _ = post(WF01, telegram_callback(ctx["man_tg"], "role:man", "Дмитрий"))
    assert_equal(status, 200)
    status, body = post(WF01, telegram_callback(ctx["man_tg"], "role:woman", "Дмитрий"))
    assert_equal(status, 200)
    assert_equal(scalar("SELECT role FROM users WHERE id=%s::uuid", (ctx["man_user_id"],)), "man")
    assert_equal(scalar("SELECT count(*) FROM profiles WHERE user_id=%s::uuid", (ctx["man_user_id"],)), 0)
    assert_true("не может быть изменена" in str(body), f"opposite role was not visibly rejected: {body}")
    return "ROLE_MAN first-wins; repeat is idempotent; opposite WOMAN callback rejected"


def test_r5():
    state = row(
        "SELECT name,onboarding_state FROM male_search_context WHERE user_id=%s::uuid",
        (ctx["man_user_id"],),
    )
    assert_equal(state["name"], "Дмитрий")
    assert_equal(state["onboarding_state"], "AWAITING_NAME_CONFIRMATION")
    post(WF01, telegram_callback(ctx["man_tg"], "man_name:change", "Дмитрий"))
    post(WF01, telegram_message(ctx["man_tg"], "Михаил", "Дмитрий"))
    post(WF01, telegram_message(ctx["man_tg"], "Москва", "Дмитрий"))
    state = row(
        "SELECT name,name_source,name_confirmed_at,city,city_normalized,onboarding_state FROM male_search_context WHERE user_id=%s::uuid",
        (ctx["man_user_id"],),
    )
    assert_equal(state["name"], "Михаил")
    assert_equal(state["name_source"], "MANUAL")
    assert_true(state["name_confirmed_at"] is not None, "manual name not confirmed")
    assert_equal(state["city_normalized"], "москва")
    assert_equal(state["onboarding_state"], "COMPLETED")
    assert_equal(scalar("SELECT count(*) FROM profiles WHERE user_id=%s::uuid", (ctx["man_user_id"],)), 0)
    return "MAN name change and city state executed in real n8n; completed MAN has no profiles row"


def test_r6():
    tg = 990000002
    post(WF01, telegram_message(tg, "/start", "Анна"))
    status, body = post(WF01, telegram_callback(tg, "role:woman", "Анна"))
    assert_equal(status, 200)
    account = row(
        "SELECT u.id::text user_id,u.role FROM users u JOIN telegram_accounts ta ON ta.user_id=u.id WHERE ta.telegram_id=%s",
        (tg,),
    )
    assert_equal(account["role"], "woman")
    profile = row("SELECT id::text FROM profiles WHERE user_id=%s::uuid AND status='DRAFT'", (account["user_id"],))
    session = row(
        "SELECT id::text,profile_id::text FROM profile_ai_sessions WHERE user_id=%s::uuid AND status='IN_PROGRESS'",
        (account["user_id"],),
    )
    assert_true(profile and session, "WOMAN profile/session missing")
    assert_equal(profile["id"], session["profile_id"])
    assert_equal(scalar("SELECT count(*) FROM profiles WHERE user_id=%s::uuid AND status='DRAFT'", (account["user_id"],)), 1)
    assert_equal(scalar("SELECT count(*) FROM profile_ai_sessions WHERE user_id=%s::uuid AND status='IN_PROGRESS'", (account["user_id"],)), 1)
    ctx.update(woman_tg=tg, woman_user_id=account["user_id"], woman_profile_id=profile["id"], woman_session_id=session["id"])
    assert_true(isinstance(body, dict), f"unexpected WOMAN reply: {body}")
    return f"profile={profile['id']}; session={session['id']}; exactly one DRAFT/IN_PROGRESS pair"


def test_r7():
    status, body = post(WF01, telegram_message(ctx["woman_tg"], "Меня зовут Анна", "Анна"), timeout=40)
    assert_equal(status, 200)
    assert_equal(scalar("SELECT name FROM profiles WHERE id=%s::uuid", (ctx["woman_profile_id"],)), "Анна")
    assert_true(isinstance(body, dict) and body.get("message"), f"WF_01 did not receive WF_03 response: {body}")
    return f"real authenticated WF_01 HTTP Request -> WF_03 Webhook persisted name; response={body.get('message')!r}"


def test_r8():
    status, body = post(WF01, telegram_photo(ctx["woman_tg"], "gate-photo-largest", "Анна"), timeout=40)
    assert_equal(status, 200)
    photos = rows(
        "SELECT telegram_file_id,position FROM profile_photos WHERE profile_id=%s::uuid ORDER BY position",
        (ctx["woman_profile_id"],),
    )
    assert_true(any(x["telegram_file_id"] == "gate-photo-largest" for x in photos), f"largest photo id not saved: {photos}")
    assert_true(isinstance(body, dict) and body.get("message"), f"photo handoff did not return response: {body}")
    return f"real PHOTO handoff saved gate-photo-largest; positions={[x['position'] for x in photos]}"


def test_r9():
    before = woman_snapshot()
    before_photos = scalar("SELECT count(*) FROM profile_photos WHERE profile_id=%s::uuid", (ctx["woman_profile_id"],))
    bad = str(uuid.uuid4())
    status, body = post(
        WF03,
        {
            "telegram_id": str(ctx["woman_tg"]),
            "chat_id": str(ctx["woman_tg"]),
            "update_type": "TEXT",
            "message_text": "bad session",
            "user_id": ctx["woman_user_id"],
            "profile_id": bad,
            "session_id": ctx["woman_session_id"],
        },
        auth=True,
        timeout=30,
    )
    assert_equal(status, 200)
    assert_true(isinstance(body, dict), f"session error response not JSON: {body}")
    assert_equal(body.get("code"), "WOMAN_SESSION_NOT_AVAILABLE")
    assert_equal(woman_snapshot(), before)
    assert_equal(scalar("SELECT count(*) FROM profile_photos WHERE profile_id=%s::uuid", (ctx["woman_profile_id"],)), before_photos)
    return "wrong profile/session tuple returned WOMAN_SESSION_NOT_AVAILABLE with no WOMAN mutation"


def test_r10():
    before = woman_snapshot()
    cases = [
        ("refused", "http://127.0.0.1:19999/unreachable", 30),
        ("400", "http://127.0.0.1:18080/handoff/400", 30),
        ("500", "http://127.0.0.1:18080/handoff/500", 30),
        ("malformed", "http://127.0.0.1:18080/handoff/malformed", 30),
        ("timeout", "http://127.0.0.1:18080/handoff/timeout", 35),
    ]
    try:
        for label, target, timeout in cases:
            restart_n8n(target)
            status, body = post(
                WF01,
                telegram_message(ctx["woman_tg"], f"handoff-failure-{label}", "Анна"),
                timeout=timeout,
            )
            assert_equal(status, 200, f"{label}: WF_01 did not return controlled HTTP response")
            assert_true("Не удалось обработать ответ" in str(body), f"{label}: fallback not returned: {body}")
            assert_equal(woman_snapshot(), before, f"{label}: WOMAN state changed on failed handoff")
    finally:
        restart_n8n(DEFAULT_WF03_TARGET)
    return "connection-refused, 4xx, 5xx, malformed-response and timeout all used WF_01 controlled fallback without state advance"


def test_r11():
    before = woman_snapshot()
    for marker in ("[MOCK_500]", "[MOCK_MALFORMED]", "[MOCK_TIMEOUT]"):
        status, body = post(WF01, telegram_message(ctx["woman_tg"], marker, "Анна"), timeout=40)
        assert_equal(status, 200)
        assert_true(isinstance(body, dict) and body.get("message"), f"AI failure did not return controlled response: {body}")
        assert_equal(woman_snapshot(), before, f"AI failure {marker} mutated WOMAN state")
    return "DeepSeek 500, malformed extraction and timeout paths returned controlled responses with no persistence/cursor/finalization"


def test_r12():
    sequence = [
        "Мне 25 лет",
        "Я живу в Москве",
        "Район Центральный",
        "Рост 170",
        "Вес 55",
        "Размер груди 3",
        "Описание: Тестовая анкета runtime gate",
        "Цена 5000",
        "Встреча в отеле",
    ]
    last_body = None
    for text in sequence:
        status, last_body = post(WF01, telegram_message(ctx["woman_tg"], text, "Анна"), timeout=40)
        assert_equal(status, 200, f"failed while completing WOMAN field: {text}")
    profile_status = scalar("SELECT status FROM profiles WHERE id=%s::uuid", (ctx["woman_profile_id"],))
    session_status = scalar("SELECT status FROM profile_ai_sessions WHERE id=%s::uuid", (ctx["woman_session_id"],))
    assert_equal(profile_status, "PENDING_MODERATION")
    assert_equal(session_status, "COMPLETED")
    assert_equal(
        scalar("SELECT count(*) FROM profile_moderation WHERE profile_id=%s::uuid AND status='PENDING'", (ctx["woman_profile_id"],)),
        1,
    )
    assert_equal(
        scalar("SELECT count(*) FROM audit_events WHERE event_type='profile_created' AND event_data->>'profile_id'=%s", (ctx["woman_profile_id"],)),
        1,
    )
    status, body = post(
        WF03,
        {
            "telegram_id": str(ctx["woman_tg"]),
            "chat_id": str(ctx["woman_tg"]),
            "update_type": "TEXT",
            "message_text": "repeat finalize",
            "user_id": ctx["woman_user_id"],
            "profile_id": ctx["woman_profile_id"],
            "session_id": ctx["woman_session_id"],
        },
        auth=True,
        timeout=30,
    )
    assert_equal(status, 200)
    assert_equal(body.get("code"), "WOMAN_SESSION_NOT_AVAILABLE")
    assert_equal(scalar("SELECT count(*) FROM profile_moderation WHERE profile_id=%s::uuid AND status='PENDING'", (ctx["woman_profile_id"],)), 1)
    assert_equal(scalar("SELECT count(*) FROM audit_events WHERE event_type='profile_created' AND event_data->>'profile_id'=%s", (ctx["woman_profile_id"],)), 1)
    return f"profile=PENDING_MODERATION; session=COMPLETED; one moderation/audit; final response={last_body}"


def seed_terminal(status, tg):
    user_id = scalar("INSERT INTO users(role) VALUES('woman') RETURNING id::text")
    with DB.cursor() as cur:
        cur.execute(
            "INSERT INTO telegram_accounts(user_id,telegram_id,username) VALUES(%s::uuid,%s,%s)",
            (user_id, tg, f"terminal_{tg}"),
        )
        cur.execute(
            "INSERT INTO profiles(user_id,status,name,age,city,city_normalized) VALUES(%s::uuid,%s,'Terminal',30,'Тестград','тестград')",
            (user_id, status),
        )
        cur.execute("INSERT INTO profiles(user_id,status) VALUES(%s::uuid,'DRAFT')", (user_id,))
    return user_id


def test_r13():
    status, body = post(WF01, telegram_message(ctx["woman_tg"], "/start", "Анна"))
    assert_equal(status, 200)
    assert_true("ожидает модерации" in str(body), f"completed WOMAN did not resume pending state: {body}")
    post(WF01, telegram_callback(ctx["woman_tg"], "role:woman", "Анна"))
    assert_equal(scalar("SELECT count(*) FROM profiles WHERE user_id=%s::uuid AND status='DRAFT'", (ctx["woman_user_id"],)), 0)
    assert_equal(scalar("SELECT count(*) FROM profile_ai_sessions WHERE user_id=%s::uuid AND status='IN_PROGRESS'", (ctx["woman_user_id"],)), 0)

    mapping = [("ACTIVE", 990000011), ("PENDING_MODERATION", 990000012), ("BLOCKED", 990000013)]
    observed = {}
    for expected, tg in mapping:
        uid = seed_terminal(expected, tg)
        status, response = post(WF01, telegram_message(tg, "/start", "Terminal"))
        assert_equal(status, 200)
        assert_true(isinstance(response, dict), f"terminal {expected}: bad response {response}")
        assert_equal(response.get("woman_state"), expected, f"terminal {expected} lost precedence over stale DRAFT")
        assert_equal(scalar("SELECT count(*) FROM profile_ai_sessions WHERE user_id=%s::uuid AND status='IN_PROGRESS'", (uid,)), 0)
        observed[expected] = response.get("message")
    return f"completed WOMAN did not restart; terminal precedence observed for ACTIVE/PENDING_MODERATION/BLOCKED: {observed}"


def insert_profile(owner_id, status, name, age, city_norm):
    return scalar(
        "INSERT INTO profiles(user_id,status,name,age,city,city_normalized,description) VALUES(%s::uuid,%s,%s,%s,%s,%s,'catalog runtime gate') RETURNING id::text",
        (owner_id, status, name, age, city_norm.title(), city_norm),
    )


def test_r14():
    man = scalar("INSERT INTO users(role) VALUES('man') RETURNING id::text")
    with DB.cursor() as cur:
        cur.execute(
            "INSERT INTO male_search_context(user_id,name,name_source,name_confirmed_at,city,city_normalized,onboarding_state) VALUES(%s::uuid,'Catalog Man','MANUAL',now(),'Каталогград','каталогград','COMPLETED')",
            (man,),
        )
    w1 = scalar("INSERT INTO users(role) VALUES('woman') RETURNING id::text")
    w2 = scalar("INSERT INTO users(role) VALUES('woman') RETURNING id::text")
    w3 = scalar("INSERT INTO users(role) VALUES('woman') RETURNING id::text")
    man_owner = scalar("INSERT INTO users(role) VALUES('man') RETURNING id::text")
    a = insert_profile(w1, "ACTIVE", "A", 25, "каталогград")
    b = insert_profile(w2, "ACTIVE", "B", 40, "каталогград")
    insert_profile(w3, "ACTIVE", "OtherCity", 25, "другойгород")
    insert_profile(w3, "PENDING_MODERATION", "Pending", 25, "каталогград")
    insert_profile(man_owner, "ACTIVE", "ManOwned", 25, "каталогград")

    status, first = post(WF05, {"user_id": man, "limit": 50, "offset": 0})
    assert_equal(status, 200)
    first_ids = [x["id"] for x in first["items"]]
    assert_equal(set(first_ids), {a, b})
    assert_true(all(float(x["match_score"]) == 0 for x in first["items"]), f"no-preference score was not zero: {first}")

    with DB.cursor() as cur:
        cur.execute(
            "INSERT INTO male_search_preferences(user_id,age_from,age_to) VALUES(%s::uuid,18,30)",
            (man,),
        )
    status, second = post(WF05, {"user_id": man, "limit": 50, "offset": 0})
    assert_equal(status, 200)
    second_ids = [x["id"] for x in second["items"]]
    assert_equal(set(second_ids), set(first_ids))
    assert_equal(second_ids[0], a, "age preference did not rank matching candidate first")
    scores = {x["id"]: float(x["match_score"]) for x in second["items"]}
    assert_true(scores[a] > scores[b], f"preferences did not affect ranking scores: {scores}")
    return f"candidate set stayed {sorted(first_ids)}; preferences only changed score/order ({scores})"


def execution_snapshot():
    db_path = ROOT / ".runtime" / "n8n-data" / "database.sqlite"
    if not db_path.exists():
        return {"available": False, "reason": "n8n sqlite database not found"}
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = conn.execute(
            "SELECT id,workflowId,status,startedAt,stoppedAt FROM execution_entity ORDER BY CAST(id AS INTEGER) DESC LIMIT 50"
        )
        data = [dict(zip([d[0] for d in cur.description], item)) for item in cur.fetchall()]
        conn.close()
        return {"available": True, "executions": data}
    except Exception as exc:
        return {"available": False, "reason": str(exc)}


def main():
    test(1, "Postgres v2.6 single JSON bind", test_r1)
    test(2, "new Telegram user registration", test_r2)
    test(3, "repeated registration idempotency", test_r3)
    test(4, "role first-wins", test_r4)
    test(5, "MAN state machine", test_r5)
    test(6, "WOMAN initial profile/session", test_r6)
    test(7, "real WF_01 to WF_03 TEXT handoff", test_r7)
    test(8, "real WF_01 to WF_03 PHOTO handoff", test_r8)
    test(9, "WF_03 stale/mismatched session", test_r9)
    test(10, "WF_01 handoff transport and HTTP failures", test_r10)
    test(11, "DeepSeek failure paths", test_r11)
    test(12, "WOMAN finalization", test_r12)
    test(13, "terminal WOMAN lifecycle precedence", test_r13)
    test(14, "WF_05 hard filters and preference ranking", test_r14)

    report = {
        "runtime": "real n8n container",
        "n8n_image": os.environ.get("N8N_IMAGE", "docker.n8n.io/n8nio/n8n:2.34.5"),
        "results": results,
        "execution_snapshot": execution_snapshot(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    failed = [x for x in results if x["status"] != "PASS"]
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    finally:
        DB.close()

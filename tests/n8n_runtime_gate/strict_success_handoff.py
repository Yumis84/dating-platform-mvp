#!/usr/bin/env python3
import os

import psycopg
import requests

BASE = "http://127.0.0.1:5678"
WF01 = f"{BASE}/webhook/runtime-gate/wf01"
FALLBACK = "Не удалось обработать ответ. Попробуйте ещё раз."
TG = 990000077


def post(payload):
    response = requests.post(WF01, json=payload, timeout=40)
    response.raise_for_status()
    return response.json()


def message(text=None, photo=None):
    body = {
        "message": {
            "message_id": 7700,
            "from": {"id": TG, "first_name": "Strict", "username": "strict_gate"},
            "chat": {"id": TG},
        }
    }
    if text is not None:
        body["message"]["text"] = text
    if photo is not None:
        body["message"]["photo"] = [
            {"file_id": f"{photo}-small"},
            {"file_id": photo},
        ]
    return body


def callback(data):
    return {
        "callback_query": {
            "id": f"strict-{data}",
            "data": data,
            "from": {"id": TG, "first_name": "Strict", "username": "strict_gate"},
            "message": {"message_id": 7700, "chat": {"id": TG}},
        }
    }


post(message(text="/start"))
post(callback("role:woman"))
text_response = post(message(text="Меня зовут Анна"))
if text_response.get("message") == FALLBACK or text_response.get("handoff_ok") is not True:
    raise SystemExit(f"TEXT success handoff UX failed: {text_response}")

photo_response = post(message(photo="strict-photo-largest"))
if photo_response.get("message") == FALLBACK or photo_response.get("handoff_ok") is not True:
    raise SystemExit(f"PHOTO success handoff UX failed: {photo_response}")

with psycopg.connect(
    host=os.environ.get("RUNTIME_GATE_PG_HOST", "127.0.0.1"),
    port=int(os.environ.get("RUNTIME_GATE_PG_PORT", "5432")),
    dbname=os.environ.get("RUNTIME_GATE_PG_DATABASE", "runtime_gate"),
    user=os.environ.get("RUNTIME_GATE_PG_USER", "runtime_gate"),
    password=os.environ["RUNTIME_GATE_PG_PASSWORD"],
) as conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT p.name,
                   EXISTS(
                     SELECT 1 FROM profile_photos ph
                     WHERE ph.profile_id=p.id AND ph.telegram_file_id='strict-photo-largest'
                   )
            FROM profiles p
            JOIN telegram_accounts ta ON ta.user_id=p.user_id
            WHERE ta.telegram_id=%s AND p.status='DRAFT'
            """,
            (TG,),
        )
        row = cur.fetchone()
        if row != ("Анна", True):
            raise SystemExit(f"Successful handoff did not persist expected data: {row}")

print("STRICT PASS: successful TEXT/PHOTO handoffs returned WF_03 messages with handoff_ok=true and persisted data")

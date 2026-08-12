#!/usr/bin/env python3
import json
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 18080


def extraction_for(message: str):
    fields = {}
    price_operations = []
    meeting_place_operations = []
    clarification = None

    if "Меня зовут Анна" in message:
        fields["name"] = "Анна"
    elif "Мне 25" in message:
        fields["age"] = 25
    elif "живу в Москве" in message:
        fields["city"] = "Москва"
    elif "Район Центральный" in message:
        fields["district"] = "Центральный"
    elif "Рост 170" in message:
        fields["height_cm"] = 170
    elif "Вес 55" in message:
        fields["weight_kg"] = 55
    elif "Размер груди 3" in message:
        fields["breast_size"] = 3
    elif message.startswith("Описание:"):
        fields["description"] = message.split(":", 1)[1].strip()
    elif "Цена 5000" in message:
        price_operations.append(
            {
                "operation": "APPEND",
                "service_name": "Встреча",
                "amount": 5000,
                "currency": "RUB",
                "duration_minutes": 60,
                "description": "Runtime gate",
            }
        )
    elif "Встреча в отеле" in message:
        meeting_place_operations.append(
            {
                "operation": "APPEND",
                "place_type": "HOTEL",
                "label": "Отель",
                "district": "Центральный",
                "description": "Runtime gate",
            }
        )
    else:
        clarification = "runtime-gate-noop"

    return {
        "fields": fields,
        "price_operations": price_operations,
        "meeting_place_operations": meeting_place_operations,
        "clarification": clarification,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "RuntimeGateMock/1.0"

    def log_message(self, fmt, *args):
        print(f"mock-ai: {self.address_string()} - {fmt % args}", flush=True)

    def _send(self, status, payload=None, raw=None, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        if raw is not None:
            self.wfile.write(raw)
        elif payload is not None:
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        if self.path == "/healthz":
            self._send(200, {"ok": True})
            return
        self._send(404, {"message": "not found"})

    def do_POST(self):
        if self.path == "/handoff/400":
            self._send(400, {"message": "runtime-gate-400"})
            return
        if self.path == "/handoff/500":
            self._send(500, {"message": "runtime-gate-500"})
            return
        if self.path == "/handoff/malformed":
            self._send(200, raw=b"{not-json", content_type="application/json")
            return
        if self.path == "/handoff/timeout":
            time.sleep(20)
            self._send(200, {"message": "too late"})
            return
        if self.path != "/v1/chat/completions":
            self._send(404, {"message": "not found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            request = json.loads(body.decode("utf-8"))
        except Exception:
            self._send(400, {"message": "invalid request json"})
            return

        user_content = ""
        try:
            user_content = request["messages"][-1]["content"]
        except Exception:
            pass

        try:
            inner = json.loads(user_content) if isinstance(user_content, str) else user_content
            message = str((inner or {}).get("message") or "")
        except Exception:
            message = str(user_content)

        if "[MOCK_TIMEOUT]" in message:
            time.sleep(20)
            self._send(200, {"choices": [{"message": {"content": "{}"}}]})
            return
        if "[MOCK_500]" in message:
            self._send(500, {"message": "mock ai failure"})
            return
        if "[MOCK_MALFORMED]" in message:
            self._send(
                200,
                {"choices": [{"message": {"content": "{malformed-ai-json"}}]},
            )
            return

        payload = extraction_for(message)
        self._send(
            200,
            {
                "id": "runtime-gate",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(payload, ensure_ascii=False),
                        }
                    }
                ],
            },
        )


if __name__ == "__main__":
    print(f"runtime gate mock listening on http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

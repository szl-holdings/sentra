#!/usr/bin/env python3
"""SZL rebuilt organ: bounded health endpoint with W3C trace echo and OTLP export.

Honest scope: this is a REBUILT organ. The historical sentra source repository is
unavailable (its last signed historical commit is recorded in
HONEST_PROVENANCE.md). This service implements exactly the szl-build-env organ
contract - GET /healthz with a W3C traceparent echo and one exported OTLP span per
request - and nothing else. No claim is made that historical sentra
functionality was restored.

Doctrine: fail closed, no egress except the explicitly configured cluster-local
OTLP endpoint, no secrets read or logged, bounded bodies, finite diagnostics.
"""
from __future__ import annotations

import ipaddress
import json
import os
import re
import secrets
import sys
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ORGAN = "sentra"
SCHEMA = "szl.organ.healthz/v2"
TRACEPARENT = re.compile(r"00-([0-9a-f]{32})-([0-9a-f]{16})-0([0-9a-f])")
MAX_EXPORT_SECONDS = 2.0


def _otlp_endpoint(raw):
    """Admit only loopback or cluster-local DNS OTLP endpoints. Fail closed."""
    if not raw or not raw.isascii() or any(c.isspace() or ord(c) < 32 for c in raw):
        return None
    parsed = urllib.parse.urlsplit(raw)
    if parsed.scheme != "http" or parsed.username or parsed.password:
        return None
    if parsed.query or parsed.fragment or parsed.path not in ("", "/"):
        return None
    host = (parsed.hostname or "").strip(".")
    if not host:
        return None
    port = parsed.port
    if port is None or not 1 <= port <= 65535:
        return None
    if host == "localhost":
        return raw
    try:
        if ipaddress.ip_address(host).is_loopback:
            return raw
    except ValueError:
        pass
    if host.endswith(".svc") or host.endswith(".svc.cluster.local"):
        return raw
    return None


def export_span(trace_id, span_id, parent_span_id, started_ns, ended_ns):
    """Export one honest SERVER span for the request actually served."""
    endpoint = _otlp_endpoint(
        os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
        or os.environ.get("SZL_OTLP_ENDPOINT", "")
    )
    if endpoint is None:
        return "OTLP_ENDPOINT_NOT_CONFIGURED"
    payload = {
        "resourceSpans": [{
            "resource": {"attributes": [
                {"key": "service.name", "value": {"stringValue": ORGAN}},
                {"key": "szl.organ", "value": {"stringValue": ORGAN}},
            ]},
            "scopeSpans": [{
                "scope": {"name": "szl-organ", "version": "2"},
                "spans": [{
                    "traceId": trace_id,
                    "spanId": span_id,
                    "parentSpanId": parent_span_id,
                    "name": "GET /healthz",
                    "kind": 2,
                    "startTimeUnixNano": started_ns,
                    "endTimeUnixNano": ended_ns,
                    "attributes": [{"key": "http.request.method", "value": {"stringValue": "GET"}}],
                    "status": {},
                }],
            }],
        }],
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    url = endpoint.rstrip("/") + "/v1/traces"
    try:
        request = urllib.request.Request(url, data=body, method="POST",
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=MAX_EXPORT_SECONDS) as response:
            if 200 <= response.status < 300:
                return None
            return "OTLP_HTTP_ERROR"
    except Exception:
        return "OTLP_EXPORT_FAILED"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "szl-organ/2"

    def log_message(self, fmt, *args):
        sys.stderr.write("organ %s: %s\n" % (ORGAN, (fmt % args)[:200]))
        sys.stderr.flush()

    def _respond(self, code, body, *, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _reject(self, code, reason):
        body = json.dumps({"schema": SCHEMA, "organ": ORGAN, "status": "error",
                           "reason": reason}).encode("utf-8")
        self._respond(code, body)

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if path != "/healthz":
            self._reject(404, "route_not_found")
            return
        header = (self.headers.get("traceparent") or "").strip()
        match = TRACEPARENT.fullmatch(header)
        if not header:
            # Plain health poll (acceptance step 3, readiness): honest health,
            # no trace context, no echo, no span.
            body = json.dumps({"schema": SCHEMA, "organ": ORGAN, "status": "ok",
                               "trace_context": False}).encode("utf-8")
            self._respond(200, body)
            return
        if not match:
            self._reject(400, "traceparent_invalid")
            return
        trace_id, parent_span_id = match.group(1), match.group(2)
        span_id = secrets.token_hex(8)
        started = time.time_ns()
        error = export_span(trace_id, span_id, parent_span_id, started, started)
        ended = time.time_ns()
        body = json.dumps({"schema": SCHEMA, "organ": ORGAN, "status": "ok",
                           "trace_context": True,
                           "span_exported": error is None}).encode("utf-8")
        self._respond(200, body, extra={"traceparent": "00-%s-%s-01" % (trace_id, span_id)})

    def do_POST(self):
        self._reject(405, "method_not_allowed")

    def do_PUT(self):
        self._reject(405, "method_not_allowed")

    def do_HEAD(self):
        self._reject(405, "method_not_allowed")


def main():
    raw_port = os.environ.get("PORT", "7860")
    if not raw_port.isdigit() or not 1 <= int(raw_port) <= 65535:
        raise SystemExit("PORT must be an integer between 1 and 65535")
    port = int(raw_port)
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    sys.stderr.write("organ %s: serving /healthz on port %d\n" % (ORGAN, port))
    sys.stderr.flush()
    server.serve_forever()


if __name__ == "__main__":
    main()

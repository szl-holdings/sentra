#!/usr/bin/env python3
"""Contract tests for the rebuilt sentra organ.

Covers the exact szl-build-env fan-out probe requirements: one traceparent
response header with the same trace id and a fresh sampled span id, strict
JSON body, content-type/length shape, route and method discipline, the
fail-closed OTLP endpoint policy, and the exported OTLP span payload.
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
import http.client

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import serve  # noqa: E402

ORGAN = "sentra"
TRACEPARENT = "00-1ed755c47f59e6eb8ba582263710492e-3d38fca2050e1e54-01"


class Collector(BaseHTTPRequestHandler):
    captured = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        Collector.captured.append(json.loads(body.decode("utf-8")))
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, fmt, *args):
        pass


class EndpointPolicyTests(unittest.TestCase):
    def test_loopback_allowed(self):
        self.assertIsNotNone(serve._otlp_endpoint("http://127.0.0.1:4318"))
        self.assertIsNotNone(serve._otlp_endpoint("http://localhost:4318"))

    def test_cluster_local_allowed(self):
        self.assertIsNotNone(serve._otlp_endpoint("http://opentelemetry-collector.szl.svc:4318"))
        self.assertIsNotNone(serve._otlp_endpoint("http://otel.szl.svc.cluster.local:4318"))

    def test_public_hosts_rejected(self):
        self.assertIsNone(serve._otlp_endpoint("http://example.com:4318"))
        self.assertIsNone(serve._otlp_endpoint("http://10.0.0.1:4318"))
        self.assertIsNone(serve._otlp_endpoint("https://opentelemetry-collector.szl.svc:4318"))
        self.assertIsNone(serve._otlp_endpoint("http://opentelemetry-collector.szl.svc:4318/prefix"))
        self.assertIsNone(serve._otlp_endpoint(""))
        self.assertIsNone(serve._otlp_endpoint("http://user:pw@opentelemetry-collector.szl.svc:4318"))
        self.assertIsNone(serve._otlp_endpoint("http://opentelemetry-collector.szl.svc"))

    def test_malformed_ports_and_types_deny_instead_of_crashing(self):
        for endpoint in (None, 42, [], "http://localhost:bad",
                         "http://localhost:65536", "http://[::1",
                         "http://example.svc:9999999"):
            with self.subTest(endpoint=endpoint):
                self.assertIsNone(serve._otlp_endpoint(endpoint))

    def test_no_proxies_used_even_when_environment_injects_proxy(self):
        builder = urllib.request.build_opener
        with patch.dict(os.environ, {"HTTP_PROXY": "http://127.0.0.1:9999",
                                     "http_proxy": "http://127.0.0.1:9999"}):
            with patch.object(serve.urllib.request, "build_opener", wraps=builder) as build:
                serve._otlp_opener()
                supplied = build.call_args.args
                handlers = [h for h in supplied if isinstance(h, urllib.request.ProxyHandler)]
                self.assertEqual(len(handlers), 1)
                self.assertEqual(handlers[0].proxies, {})
                self.assertTrue(any(isinstance(h, serve._NoRedirect) for h in supplied))


class OrganContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Collector.captured = []
        cls.collector = ThreadingHTTPServer(("127.0.0.1", 0), Collector)
        cls.collector_port = cls.collector.server_address[1]
        threading.Thread(target=cls.collector.serve_forever, daemon=True).start()
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://127.0.0.1:%d" % cls.collector_port
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.collector.shutdown()

    def request(self, path="/healthz", method="GET", headers=None):
        url = "http://127.0.0.1:%d%s" % (self.port, path)
        request = urllib.request.Request(url, method=method, headers=headers or {})
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as error:
            return error.code, dict(error.headers), error.read()

    def test_healthz_echoes_fresh_sampled_span(self):
        status, headers, body = self.request(headers={"traceparent": TRACEPARENT})
        self.assertEqual(status, 200)
        echoed = headers.get("traceparent")
        self.assertIsNotNone(echoed)
        match = re.fullmatch(r"00-([0-9a-f]{32})-([0-9a-f]{16})-0([0-9a-f])", echoed)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "1ed755c47f59e6eb8ba582263710492e")
        self.assertNotEqual(match.group(2), "3d38fca2050e1e54")
        self.assertEqual(match.group(3), "1")
        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(payload, {"schema": "szl.organ.healthz/v2", "organ": ORGAN,
                                  "status": "ok", "trace_context": True,
                                  "span_exported": True})
        self.assertEqual(headers.get("Content-Type"), "application/json")

    def test_plain_health_without_traceparent(self):
        status, headers, body = self.request()
        self.assertEqual(status, 200)
        self.assertIsNone(headers.get("traceparent"))
        self.assertEqual(json.loads(body), {"schema": "szl.organ.healthz/v2",
                                          "organ": ORGAN, "status": "ok",
                                          "trace_context": False})

    def test_healthz_rejects_invalid_traceparent(self):
        for bad in ("garbage", "ff-" + "a" * 32 + "-" + "b" * 16 + "-01",
                    "00-" + "A" * 32 + "-" + "b" * 16 + "-01",
                    "00-" + "0" * 32 + "-" + "b" * 16 + "-01",
                    "00-" + "a" * 32 + "-" + "0" * 16 + "-01",
                    "00-" + "a" * 32 + "-" + "b" * 16 + "-00",
                    TRACEPARENT + " "):
            status, _, body = self.request(headers={"traceparent": bad})
            self.assertEqual(status, 400, bad[:20])
            self.assertEqual(json.loads(body)["reason"], "traceparent_invalid")

    def test_duplicate_traceparent_denied(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.putrequest("GET", "/healthz")
            connection.putheader("traceparent", TRACEPARENT)
            connection.putheader("traceparent", TRACEPARENT)
            connection.endheaders()
            response = connection.getresponse()
            self.assertEqual(response.status, 400)
            self.assertEqual(json.loads(response.read())["reason"], "traceparent_invalid")
        finally:
            connection.close()

    def test_empty_traceparent_header_denied(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.putrequest("GET", "/healthz")
            connection.putheader("traceparent", "")
            connection.endheaders()
            response = connection.getresponse()
            self.assertEqual(response.status, 400)
            self.assertEqual(json.loads(response.read())["reason"], "traceparent_invalid")
        finally:
            connection.close()

    def test_export_failure_fails_closed_without_echo(self):
        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://example.com:4318"}):
            status, headers, body = self.request(headers={"traceparent": TRACEPARENT})
        self.assertEqual(status, 503)
        self.assertIsNone(headers.get("traceparent"))
        self.assertEqual(json.loads(body)["reason"], "trace_export_unavailable")

    def test_redirect_cannot_export_to_unreviewed_target(self):
        class Destination(BaseHTTPRequestHandler):
            hits = 0

            def do_GET(self):
                type(self).hits += 1
                self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def do_POST(self):
                type(self).hits += 1
                self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args):
                pass

        class Redirect(BaseHTTPRequestHandler):
            location = ""

            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                self.send_response(302)
                self.send_header("Location", self.location)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args):
                pass

        destination = ThreadingHTTPServer(("127.0.0.1", 0), Destination)
        redirector = ThreadingHTTPServer(("127.0.0.1", 0), Redirect)
        Redirect.location = "http://127.0.0.1:%d/leak" % destination.server_address[1]
        threads = []
        for server in (destination, redirector):
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            threads.append(thread)
        try:
            with patch.dict(os.environ, {
                "OTEL_EXPORTER_OTLP_ENDPOINT": "http://127.0.0.1:%d" % redirector.server_address[1],
                "HTTP_PROXY": "http://127.0.0.1:9999",
            }):
                result = serve.export_span("a" * 32, "b" * 16, "c" * 16, 1, 2)
            self.assertIsNotNone(result)
            self.assertEqual(Destination.hits, 0)
        finally:
            for server in (redirector, destination):
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=3)

    def test_unknown_route_404(self):
        status, _, body = self.request(path="/")
        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body)["reason"], "route_not_found")

    def test_post_rejected(self):
        status, _, body = self.request(method="POST")
        self.assertEqual(status, 405)
        self.assertEqual(json.loads(body)["reason"], "method_not_allowed")

    def test_span_exported_to_collector(self):
        Collector.captured = []
        before = time.time_ns()
        self.request(headers={"traceparent": TRACEPARENT})
        deadline = time.time() + 5
        while not Collector.captured and time.time() < deadline:
            time.sleep(0.05)
        self.assertEqual(len(Collector.captured), 1)
        export = Collector.captured[0]
        resource = export["resourceSpans"][0]["resource"]["attributes"]
        self.assertIn({"key": "service.name", "value": {"stringValue": ORGAN}}, resource)
        span = export["resourceSpans"][0]["scopeSpans"][0]["spans"][0]
        self.assertEqual(span["traceId"], "1ed755c47f59e6eb8ba582263710492e")
        self.assertEqual(span["parentSpanId"], "3d38fca2050e1e54")
        self.assertTrue(span["startTimeUnixNano"] >= before)
        self.assertEqual(span["name"], "GET /healthz")


if __name__ == "__main__":
    unittest.main()

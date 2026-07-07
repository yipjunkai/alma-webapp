"""Request-ID middleware and structured logging."""

import json
import logging

from fastapi.testclient import TestClient

from app.core.logging import JsonFormatter, RequestIdFilter, request_id_ctx


def test_response_has_request_id_header(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.headers.get("x-request-id")


def test_incoming_request_id_is_echoed(client: TestClient) -> None:
    response = client.get("/api/health", headers={"X-Request-ID": "req-test-123"})
    assert response.headers["x-request-id"] == "req-test-123"


def test_security_headers_present(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "no-referrer" in response.headers["referrer-policy"]
    assert "max-age" in response.headers["strict-transport-security"]
    # The API surface gets a locked-down CSP.
    assert (
        response.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"
    )


def test_request_id_filter_injects_context_id() -> None:
    token = request_id_ctx.set("ctx-1")
    try:
        record = logging.makeLogRecord({"msg": "x"})
        RequestIdFilter().filter(record)
        assert record.__dict__["request_id"] == "ctx-1"
    finally:
        request_id_ctx.reset(token)


def test_json_formatter_includes_request_id_and_extras() -> None:
    record = logging.makeLogRecord(
        {
            "name": "app.access",
            "levelname": "INFO",
            "levelno": logging.INFO,
            "msg": "request",
            "request_id": "req-42",
            "method": "GET",
            "status": 200,
        }
    )
    data = json.loads(JsonFormatter().format(record))
    assert data["message"] == "request"
    assert data["request_id"] == "req-42"
    assert data["method"] == "GET"
    assert data["status"] == 200
    assert data["level"] == "INFO"

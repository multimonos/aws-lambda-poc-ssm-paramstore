import json
import base64
from typing import Any


def payload_from_event(event: dict[str, Any]) -> dict[str, Any]:
    """extract payload from aws lambda event"""
    body = event.get("body")

    if body is not None:
        # don't catch anything
        if event.get("isBase64Encoded", False):
            decoded = base64.b64decode(body)
            return json.loads(decoded)
        else:
            return json.loads(body)

    return event


def std_response(status: int = 200, body: dict = {}) -> dict[str, Any]:
    """create a lambda fn response"""
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def error_response(code: int, message: str) -> dict[str, Any]:
    """error response convenience method"""
    body = {"error": {"message": message}}
    return std_response(code, body)


def success_response(code: int = 200, body: dict | None = None) -> dict[str, Any]:
    """success response convenience method"""
    if not body:
        body = {"message": "ok"}
    return std_response(code, body)

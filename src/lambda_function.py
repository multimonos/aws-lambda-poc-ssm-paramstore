from dataclasses import dataclass
import os
import json
import boto3
from util import error_response, payload_from_event, success_response
from typing import Any


ENV = os.environ.get("ENVIRONMENT")
REGION = os.environ.get("REGION")

ssm = boto3.client("ssm", region_name=REGION)


def get_store_host(ssm_client, env: str, business: str, store: str) -> str | None:
    path = f"/{env}/business/{business}/store/{store}/host"
    res = ssm_client.get_parameter(Name=path, WithDecryption=True)
    return res.get("Parameter", {}).get("Value")


def get_all_hosts(ssm_client, env: str, business: str) -> list[str]:
    path = f"/{env}/business/{business}/"
    next_tok = None
    hosts = []

    while True:
        kwargs = {"Path": path, "Recursive": True, "WithDecryption": True}
        if next_tok:
            kwargs["NextToken"] = next_tok

        res = ssm_client.get_parameters_by_path(**kwargs)

        for param in res.get("Parameters", []):
            if param["Name"].endswith("/host"):
                hosts.append(param["Value"])

        next_tok = res.get("NextToken")

        if not next_tok:
            break

    return hosts


@dataclass
class LambdaParams:
    business: str
    store: str

    def __post_init__(self):
        if not self.business:
            raise ValueError("Invalid business")
        if not self.store:
            raise ValueError("Invalid store")

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "LambdaParams":
        return cls(
            business=payload.get("business", ""),
            store=payload.get("store", ""),
        )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    if not ENV:
        return error_response(500, "Missing required env param.")
    if not REGION:
        return error_response(500, "Missing required env param.")

    # payload
    payload = payload_from_event(event)

    try:
        params = LambdaParams.from_payload(payload)
    except ValueError as e:
        return error_response(400, f"{e}")

    # get param
    try:
        if params.store == "*":
            value = get_all_hosts(ssm, ENV, params.business)
        else:
            value = get_store_host(ssm, ENV, params.business, params.store)

        return success_response(
            200,
            {"message": "ok", "value": json.dumps(value), "payload": params.__dict__},
        )

    except ssm.exceptions.ParameterNotFound:
        return error_response(404, "Not found.")

    except Exception as e:
        return error_response(500, f"An unknown system error occurred {e}.")

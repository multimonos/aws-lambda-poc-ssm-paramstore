import re
from dataclasses import dataclass
import pytest
import os
import json
import boto3
from typing import Type, cast
from mypy_boto3_lambda import LambdaClient


@dataclass
class Functions:
    dev: str
    prd: str


@pytest.fixture
def client() -> LambdaClient:
    client: LambdaClient = cast(LambdaClient, boto3.client("lambda"))
    return client


@pytest.fixture
def fn() -> str:
    return "dev-poc-ssm"


@pytest.mark.parametrize(
    "env,store,exp_type,exp_reg",
    [
        ("dev", "0020", str, r"^192\.168\.1\.\d{1,3}$"),
        ("dev", "*", list, r"^192\.168\.1\.\d{1,3}$"),
        ("prod", "0020", str, r"^192\.168\.100\.\d{1,3}$"),
        ("prod", "*", list, r"^192\.168\.100\.\d{1,3}$"),
    ],
)
def test_invoke(
    client: LambdaClient,
    fn: str,
    env: str,
    store: str,
    exp_type: Type,
    exp_reg: str,
):
    print("params:", fn, env, store, exp_type, exp_reg)

    payload = json.dumps({"business": "first", "store": store})
    print("payload:", payload)

    response = client.invoke(FunctionName=fn, Payload=payload)
    print("response", response)

    raw = json.loads(response.get("Payload").read().decode())
    print("raw:", raw)

    value = json.loads(raw.get("body", "{}")).get("value")
    print("value:", value)

    assert value is not None
    assert isinstance(value, exp_type)

    if isinstance(value, list):
        for host in value:
            assert re.match(exp_reg, host)
    else:
        assert re.match(exp_reg, value)

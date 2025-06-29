import pytest
import re
import boto3
from mypy_boto3_ssm import SSMClient
from typing import cast


@pytest.fixture
def ssm() -> SSMClient:
    ssm: SSMClient = cast(SSMClient, boto3.client("ssm"))
    return ssm


def test_get_single(ssm: SSMClient):
    path = f"/dev/business/first/store/0020/host"
    exp = "192.168.1.20"

    res = ssm.get_parameter(Name=path, WithDecryption=True)

    assert res.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200
    assert res.get("Parameter", {}).get("Value") == exp


def test_get_single_notfound_raises(ssm: SSMClient):
    path = f"/dev/business/first/store/9999/host"

    with pytest.raises(ssm.exceptions.ParameterNotFound):
        ssm.get_parameter(Name=path, WithDecryption=True)


def test_get_first_page(ssm: SSMClient):
    """has a hard limit of 10 ... see the lambda fn get_all_hosts()"""
    path = "/dev/business/first/"

    res = ssm.get_parameters_by_path(Path=path, Recursive=True, WithDecryption=True)

    assert isinstance(res.get("Parameters"), list)

    # only a max of 10 are retrieved
    assert len(res.get("Parameters", [])) == 10

    for param in res.get("Parameters", []):
        assert re.match(r"^192\.168\.1\.\d{1,3}$", param.get("Value", ""))

        parts = param.get("Name", "").split("/")
        assert len(parts) == 7

        store_id = parts[-2]
        assert re.match(r"^[0-9]{4}$", store_id)


def test_get_all(ssm: SSMClient):
    """get all requires paged approach"""

    path = "/dev/business/first/"
    hosts = []

    # retrieve
    next_tok = None

    while True:
        kwargs = {"Path": path, "Recursive": True, "WithDecryption": True}

        if next_tok:
            kwargs["NextToken"] = next_tok

        res = ssm.get_parameters_by_path(**kwargs)

        for param in res.get("Parameters", []):
            if param.get("Name", "").endswith("/host"):
                hosts.append(param.get("Value"))

        next_tok = res.get("NextToken")

        if not next_tok:
            break

    # validate
    assert len(hosts) > 10  # more than a single page

    for host in hosts:
        assert re.match(r"192\.168\.1\.\d{1,3}", host)


def test_get_many_failed_does_not_throw(ssm: SSMClient):
    path = "/dev/business/foobar/"
    res = ssm.get_parameters_by_path(Path=path, Recursive=True, WithDecryption=True)

    assert isinstance(res.get("Parameters"), list)
    assert len(res.get("Parameters", [])) == 0

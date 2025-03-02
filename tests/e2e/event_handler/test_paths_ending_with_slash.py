import pytest
from requests import HTTPError, Request

from tests.e2e.utils import data_fetcher


@pytest.fixture
def alb_basic_listener_endpoint(infrastructure: dict) -> str:
    dns_name = infrastructure.get("ALBDnsName")
    port = infrastructure.get("ALBBasicListenerPort", "")
    return f"http://{dns_name}:{port}"


@pytest.fixture
def alb_multi_value_header_listener_endpoint(infrastructure: dict) -> str:
    dns_name = infrastructure.get("ALBDnsName")
    port = infrastructure.get("ALBMultiValueHeaderListenerPort", "")
    return f"http://{dns_name}:{port}"


@pytest.fixture
def apigw_rest_endpoint(infrastructure: dict) -> str:
    return infrastructure.get("APIGatewayRestUrl", "")


@pytest.fixture
def apigw_http_endpoint(infrastructure: dict) -> str:
    return infrastructure.get("APIGatewayHTTPUrl", "")


@pytest.fixture
def lambda_function_url_endpoint(infrastructure: dict) -> str:
    return infrastructure.get("LambdaFunctionUrl", "")


def test_api_gateway_rest_trailing_slash(apigw_rest_endpoint):
    # GIVEN API URL ends in a trailing slash
    url = f"{apigw_rest_endpoint}todos/"
    body = "Hello World"

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            json={"body": body},
        )
    )

    # THEN expect a HTTP 200 response
    assert response.status_code == 200


def test_api_gateway_http_trailing_slash(apigw_http_endpoint):
    # GIVEN the URL for the API ends in a trailing slash API gateway should return a 404
    url = f"{apigw_http_endpoint}todos/"
    body = "Hello World"

    # WHEN calling an invalid URL (with trailing slash) expect HTTPError exception from data_fetcher
    with pytest.raises(HTTPError):
        data_fetcher.get_http_response(
            Request(
                method="POST",
                url=url,
                json={"body": body},
            )
        )


def test_lambda_function_url_trailing_slash(lambda_function_url_endpoint):
    # GIVEN the URL for the API ends in a trailing slash it should behave as if there was not one
    url = f"{lambda_function_url_endpoint}todos/"  # the function url endpoint already has the trailing /
    body = "Hello World"

    # WHEN calling an invalid URL (with trailing slash) expect HTTPError exception from data_fetcher
    with pytest.raises(HTTPError):
        data_fetcher.get_http_response(
            Request(
                method="POST",
                url=url,
                json={"body": body},
            )
        )


def test_alb_url_trailing_slash(alb_multi_value_header_listener_endpoint):
    # GIVEN url has a trailing slash - it should behave as if there was not one
    url = f"{alb_multi_value_header_listener_endpoint}/todos/"
    body = "Hello World"

    # WHEN calling an invalid URL (with trailing slash) expect HTTPError exception from data_fetcher
    with pytest.raises(HTTPError):
        data_fetcher.get_http_response(
            Request(
                method="POST",
                url=url,
                json={"body": body},
            )
        )

import pytest
from flask import jsonify, request
from flask_openapi3.blueprint import APIBlueprint
from pydantic import BaseModel, ConfigDict
from werkzeug.exceptions import BadRequest

from exceptions.base import DomainError
from exceptions.handlers import object_body


@pytest.fixture
def error_app(app):
    # Test-only routes exercise real Flask/Pydantic boundaries, never production debug routes.
    blueprint = APIBlueprint("boundary_test", __name__)

    class InputSchema(BaseModel):
        model_config = ConfigDict(extra="forbid")
        name: str

    blueprint.before_request(object_body)

    @blueprint.post("/_validation", responses={200: InputSchema})
    def validate(body: InputSchema):
        return jsonify(body.model_dump(mode="json"))

    @app.post("/_json")
    def json_body():
        return request.get_json()

    @app.get("/_domain")
    def domain():
        raise DomainError("SQL private_password")

    @app.get("/_invalid_output")
    def invalid_output():
        return InputSchema.model_validate({"name": None})

    @app.get("/_http")
    def http():
        raise BadRequest("private_password")

    @app.get("/_unexpected")
    def unexpected():
        raise RuntimeError("SQL private_password")

    app.register_api(blueprint)
    return app


@pytest.mark.parametrize(
    "path,method,status",
    [
        ("/missing", "get", 404),
        ("/health", "post", 405),
        ("/_domain", "get", 400),
        ("/_invalid_output", "get", 500),
        ("/_http", "get", 400),
        ("/_unexpected", "get", 500),
    ],
)
def test_consistent_safe_problem_details(error_app, path, method, status, capsys):
    response = getattr(error_app.test_client(), method)(path, headers={"Accept": "text/html"})
    assert response.status_code == status
    assert response.mimetype == "application/problem+json"
    assert set(response.json) == {"type", "title", "status", "detail"}
    assert response.json["status"] == status
    assert response.json["type"] == "about:blank"
    assert "private_password" not in response.text
    assert "private_password" not in capsys.readouterr().err
    if status == 405:
        assert {"GET", "HEAD", "OPTIONS"} <= set(
            response.headers["Allow"].replace(" ", "").split(",")
        )


@pytest.mark.parametrize("path", ["/_json", "/_validation"])
def test_malformed_json_uses_problem_details(error_app, path):
    response = error_app.test_client().post(
        path, data="{broken private_password", content_type="application/json"
    )
    assert response.status_code == 400
    assert response.mimetype == "application/problem+json"
    assert "private_password" not in response.text


def test_pydantic_validation_uses_400_and_unknown_fields_are_rejected(error_app):
    client = error_app.test_client()
    for data in [{}, {"name": "valid", "unexpected": "private_password"}]:
        response = client.post("/_validation", json=data)
        assert response.status_code == 400
        assert response.mimetype == "application/problem+json"
        assert "private_password" not in response.text
    assert client.post("/_validation", json={"name": "valid"}).json == {"name": "valid"}


def test_non_json_body_is_safe_415(error_app):
    response = error_app.test_client().post(
        "/_json", data="private_password", content_type="text/plain"
    )
    assert response.status_code == 415
    assert response.mimetype == "application/problem+json"
    assert "private_password" not in response.text


@pytest.mark.parametrize("field", ["item_id", "action_id", "unexpected"])
@pytest.mark.parametrize(
    "path,body",
    [
        ("/items", {"name": "valid"}),
        (
            "/actions",
            {
                "name": "valid",
                "type": "create",
                "itemId": "11111111-1111-4111-8111-111111111111",
            },
        ),
        (
            "/items/11111111-1111-4111-8111-111111111111/actions",
            {"name": "valid", "type": "create"},
        ),
    ],
)
def test_forbidden_body_fields_are_not_path_errors(app, path, body, field):
    response = app.test_client().post(path, json={**body, field: "private_password"})
    assert response.status_code == 400
    assert response.mimetype == "application/problem+json"
    assert response.json["detail"] == "The request could not be understood."


@pytest.mark.parametrize("resource", ["items", "actions"])
def test_zero_path_identity_retains_invalid_values_detail(app, resource):
    response = app.test_client().get(f"/{resource}/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 400
    assert response.json["detail"] == "The request contains invalid values."


@pytest.mark.parametrize("field", ["item_id", "action_id"])
def test_query_identity_names_are_not_path_context(app, field):
    blueprint = APIBlueprint("query_boundary", __name__)

    class QuerySchema(BaseModel):
        item_id: int
        action_id: int

    @blueprint.get("/_query")
    def query_boundary(query: QuerySchema):
        return jsonify(query.model_dump())

    app.register_api(blueprint)
    values = {"item_id": "1", "action_id": "1", field: "invalid"}
    response = app.test_client().get("/_query", query_string=values)
    assert response.status_code == 400
    assert response.json["detail"] == "The request could not be understood."

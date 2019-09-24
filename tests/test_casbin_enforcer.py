import pytest
from casbin.enforcer import Enforcer
from flask import request, jsonify
from casbin_sqlalchemy_adapter import Adapter
from casbin_sqlalchemy_adapter import Base
from casbin_sqlalchemy_adapter import CasbinRule
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_casbin import CasbinEnforcer


@pytest.fixture
def enforcer(app_fixture):
    engine = create_engine("sqlite://")
    adapter = Adapter(engine)

    session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    s = session()
    s.query(CasbinRule).delete()
    s.add(CasbinRule(ptype="p", v0="alice", v1="/item", v2="GET"))
    s.add(CasbinRule(ptype="p", v0="bob", v1="/item", v2="GET"))
    s.add(CasbinRule(ptype="p", v0="data2_admin", v1="/item", v2="POST"))
    s.add(CasbinRule(ptype="p", v0="data2_admin", v1="/item", v2="DELETE"))
    s.add(CasbinRule(ptype="p", v0="data2_admin", v1="/item", v2="GET"))
    s.add(CasbinRule(ptype="g", v0="alice", v1="data2_admin"))
    s.add(CasbinRule(ptype="g", v0="users", v1="data2_admin"))
    s.commit()
    s.close()

    yield CasbinEnforcer(app_fixture, adapter)


@pytest.mark.parametrize(
    "header, user, method, status",
    [
        ("X-User", "alice", "GET", 200),
        ("X-User", "alice", "POST", 201),
        ("X-User", "alice", "DELETE", 202),
        ("X-User", "bob", "GET", 200),
        ("X-User", "bob", "POST", 401),
        ("X-User", "bob", "DELETE", 401),
        ("X-Idp-Groups", "admin", "GET", 401),
        ("X-Idp-Groups", "users", "GET", 200),
        ("Authorization", "Basic Ym9iOnBhc3N3b3Jk", "GET", 200),
        ("Authorization", "Unsupported Ym9iOnBhc3N3b3Jk", "GET", 401),
    ],
)
def test_enforcer(app_fixture, enforcer, header, user, method, status):
    @app_fixture.route("/")
    @enforcer.enforcer
    def index():
        return jsonify({"message": "passed"}), 200

    @app_fixture.route("/item", methods=["GET", "POST", "DELETE"])
    @enforcer.enforcer
    def item():
        if request.method == "GET":
            return jsonify({"message": "passed"}), 200
        elif request.method == "POST":
            return jsonify({"message": "passed"}), 201
        elif request.method == "DELETE":
            return jsonify({"message": "passed"}), 202

    headers = {header: user}
    c = app_fixture.test_client()
    # c.post('/add', data=dict(title='2nd Item', text='The text'))
    rv = c.get("/")
    assert rv.status_code == 401
    caller = getattr(c, method.lower())
    rv = caller("/item", headers=headers)
    assert rv.status_code == status


def test_manager(app_fixture, enforcer):
    @app_fixture.route("/manager", methods=["POST"])
    @enforcer.manager
    def manager(manager):
        assert isinstance(manager, Enforcer)
        return jsonify({"message": "passed"}), 201

    c = app_fixture.test_client()
    c.post("/manager")

"""Tests for password reset/change, email verification, revocation, and claims."""
import unittest

import jwt as pyjwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Field, create_engine

from fastauth import FastAuth, User


SECRET = "account-flow-test-secret-key-0123456789"


class AccountFlowTestCase(unittest.TestCase):
    """Base: fresh app + one registered user per test, tokens captured by hooks."""

    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.auth = FastAuth(secret_key=SECRET, engine=self.engine)
        SQLModel.metadata.create_all(self.engine)

        self.delivered = {}

        @self.auth.on_password_reset
        def capture_reset(user, token):
            self.delivered["reset"] = token

        @self.auth.on_email_verify
        def capture_verify(user, token):
            self.delivered["verify"] = token

        self.app = FastAPI()
        self.auth.setup(self.app)

        @self.app.get("/verified-only")
        def verified_only(user: User = Depends(self.auth.verified_user)):
            return {"user": user.username}

        self.client = TestClient(self.app)
        response = self.client.post("/users", json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "password-1",
        })
        assert response.status_code == 201
        self.client.cookies.clear()

    def login(self, password="password-1", expect=200):
        response = self.client.post(
            "/token", data={"username": "alice", "password": password}
        )
        self.assertEqual(response.status_code, expect)
        self.client.cookies.clear()
        return response.json() if expect == 200 else None

    def headers(self, password="password-1"):
        return {"Authorization": f"Bearer {self.login(password)['access_token']}"}


class TestPasswordReset(AccountFlowTestCase):
    def test_forgot_does_not_reveal_accounts(self):
        response = self.client.post("/password/forgot", json={"email": "nobody@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("reset", self.delivered)

    def test_full_reset_flow(self):
        old_headers = self.headers()

        response = self.client.post("/password/forgot", json={"email": "alice@example.com"})
        self.assertEqual(response.status_code, 200)
        token = self.delivered["reset"]

        response = self.client.post(
            "/password/reset", json={"token": token, "new_password": "new-password-2"}
        )
        self.assertEqual(response.status_code, 200)

        # New password works, old one doesn't
        self.login(password="new-password-2")
        self.login(password="password-1", expect=401)

        # Tokens issued before the reset are revoked
        response = self.client.get("/users/me", headers=old_headers)
        self.assertEqual(response.status_code, 401)

        # The reset token is single-use
        response = self.client.post(
            "/password/reset", json={"token": token, "new_password": "another-pass-3"}
        )
        self.assertEqual(response.status_code, 401)

    def test_reset_enforces_password_rules(self):
        self.client.post("/password/forgot", json={"email": "alice@example.com"})
        response = self.client.post(
            "/password/reset", json={"token": self.delivered["reset"], "new_password": "x"}
        )
        self.assertEqual(response.status_code, 422)

    def test_reset_without_hook_prints_in_dev(self):
        auth = FastAuth(secret_key=SECRET, engine=self.engine)  # no hooks registered
        app = FastAPI()
        auth.setup(app)
        client = TestClient(app)
        response = client.post("/password/forgot", json={"email": "alice@example.com"})
        self.assertEqual(response.status_code, 200)  # falls back to console print


class TestPasswordChange(AccountFlowTestCase):
    def test_change_requires_correct_current_password(self):
        response = self.client.post(
            "/password/change",
            json={"current_password": "wrong", "new_password": "new-password-2"},
            headers=self.headers(),
        )
        self.assertEqual(response.status_code, 401)

    def test_change_rotates_password_and_revokes_tokens(self):
        headers = self.headers()
        response = self.client.post(
            "/password/change",
            json={"current_password": "password-1", "new_password": "new-password-2"},
            headers=headers,
        )
        self.assertEqual(response.status_code, 200)

        self.login(password="new-password-2")
        response = self.client.get("/users/me", headers=headers)
        self.assertEqual(response.status_code, 401)


class TestEmailVerification(AccountFlowTestCase):
    def test_verified_dependency_blocks_then_allows(self):
        headers = self.headers()

        response = self.client.get("/verified-only", headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"]["code"], "FASTAUTH_EMAIL_NOT_VERIFIED"
        )

        response = self.client.post("/email/verify/request", headers=headers)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/email/verify", json={"token": self.delivered["verify"]}
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/verified-only", headers=headers)
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/users/me", headers=headers)
        self.assertTrue(response.json()["email_verified"])


class TestRevocationAndClaims(AccountFlowTestCase):
    def test_logout_all_revokes_every_token(self):
        headers_one = self.headers()
        headers_two = self.headers()

        response = self.client.post("/logout/all", headers=headers_one)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.client.get("/users/me", headers=headers_one).status_code, 401)
        self.assertEqual(self.client.get("/users/me", headers=headers_two).status_code, 401)

        # A fresh login works again
        self.assertEqual(self.client.get("/users/me", headers=self.headers()).status_code, 200)

    def test_refresh_token_is_revoked_too(self):
        tokens = self.login()
        self.client.post("/logout/all", headers={
            "Authorization": f"Bearer {self.login()['access_token']}"
        })
        response = self.client.post(
            "/token/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        self.assertEqual(response.status_code, 401)

    def test_custom_claims_hook(self):
        @self.auth.token_claims
        def claims(user):
            return {"plan": "premium", "uid": user.id}

        tokens = self.login()
        payload = pyjwt.decode(tokens["access_token"], SECRET, algorithms=["HS256"])
        self.assertEqual(payload["plan"], "premium")
        self.assertEqual(payload["uid"], 1)


class TestCustomModelGuardrail(unittest.TestCase):
    def test_wrong_tablename_is_a_clear_error(self):
        class WrongUser(SQLModel):
            __tablename__ = "customuser"
            id: int = Field(default=None, primary_key=True)

        engine = create_engine("sqlite://")
        with self.assertRaises(ValueError) as ctx:
            FastAuth(secret_key=SECRET, engine=engine, user_model=WrongUser)
        self.assertIn("__tablename__", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)

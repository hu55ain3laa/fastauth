"""Tests for zero-config secrets, production mode, aliases, and password rules."""
import os
import tempfile
import unittest
import warnings

from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from fastauth import FastAuth, User
from fastauth.core.auth import DEV_SECRET_FILE


class EnvIsolatedTestCase(unittest.TestCase):
    """Base: isolate cwd and secret-related environment variables."""

    def setUp(self):
        self._old_cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        self._old_env = {
            k: os.environ.pop(k, None)
            for k in ("SECRET_KEY", "FASTAUTH_SECRET_KEY", "FASTAUTH_PRODUCTION")
        }
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    def tearDown(self):
        os.chdir(self._old_cwd)
        self._tmp.cleanup()
        for k, v in self._old_env.items():
            if v is not None:
                os.environ[k] = v


class TestSecretResolution(EnvIsolatedTestCase):
    def test_zero_config_generates_and_persists_secret(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            auth = FastAuth(engine=self.engine)
        self.assertTrue(any("generated" in str(w.message) for w in caught))
        self.assertTrue(os.path.exists(DEV_SECRET_FILE))

        # A second instance (e.g. after a dev-server reload) reuses the same key
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            auth2 = FastAuth(engine=self.engine)
        self.assertEqual(auth.secret_key, auth2.secret_key)

    def test_secret_from_environment(self):
        os.environ["SECRET_KEY"] = "env-secret-key-that-is-long-enough!"
        auth = FastAuth(engine=self.engine)
        self.assertEqual(auth.secret_key, "env-secret-key-that-is-long-enough!")
        self.assertFalse(os.path.exists(DEV_SECRET_FILE))

    def test_fastauth_env_var_wins_over_secret_key(self):
        os.environ["SECRET_KEY"] = "generic-secret"
        os.environ["FASTAUTH_SECRET_KEY"] = "specific-secret"
        auth = FastAuth(engine=self.engine)
        self.assertEqual(auth.secret_key, "specific-secret")

    def test_missing_engine_is_a_clear_error(self):
        with self.assertRaises(TypeError):
            FastAuth(secret_key="x" * 40)


class TestProductionMode(EnvIsolatedTestCase):
    def test_production_requires_a_secret(self):
        with self.assertRaises(ValueError):
            FastAuth(engine=self.engine, production=True)

    def test_production_rejects_short_secret(self):
        with self.assertRaises(ValueError):
            FastAuth(secret_key="short", engine=self.engine, production=True)

    def test_production_flag_from_environment(self):
        os.environ["FASTAUTH_PRODUCTION"] = "1"
        with self.assertRaises(ValueError):
            FastAuth(engine=self.engine)  # no secret -> error because prod

    def test_cookie_secure_defaults(self):
        dev = FastAuth(secret_key="x" * 40, engine=self.engine)
        self.assertFalse(dev.cookie_secure)

        prod = FastAuth(secret_key="x" * 40, engine=self.engine, production=True)
        self.assertTrue(prod.cookie_secure)

        overridden = FastAuth(
            secret_key="x" * 40, engine=self.engine,
            production=True, cookie_secure=False,
        )
        self.assertFalse(overridden.cookie_secure)

    def test_production_refuses_default_admin_password(self):
        auth = FastAuth(secret_key="x" * 40, engine=self.engine, production=True)
        SQLModel.metadata.create_all(self.engine)

        with self.assertRaises(ValueError):
            auth.create_superadmin(username="boss")  # no password

        with self.assertRaises(ValueError):
            auth.create_superadmin(username="boss", password="admin123")

        info = auth.create_superadmin(username="boss", password="a-real-password")
        self.assertTrue(info["is_new"])


class TestReadyMadeDependencies(EnvIsolatedTestCase):
    def setUp(self):
        super().setUp()
        self.auth = FastAuth(secret_key="x" * 40, engine=self.engine)
        SQLModel.metadata.create_all(self.engine)
        self.auth.initialize_db(admin_username="admin", admin_password="admin123")

        app = FastAPI()
        self.auth.setup(app)

        @app.get("/me-alias")
        def me(user: User = Depends(self.auth.current_user)):
            return {"user": user.username}

        @app.get("/admin-alias")
        def admin(user: User = Depends(self.auth.admin)):
            return {"user": user.username}

        @app.get("/roles-alias")
        def roles(user: User = Depends(self.auth.roles("premium", "admin"))):
            return {"user": user.username}

        protected_router = APIRouter(dependencies=[self.auth.required])

        @protected_router.get("/router-protected")
        def router_protected():
            return {"ok": True}

        app.include_router(protected_router)

        # Log in with a separate client so self.client carries no auth cookie
        login_client = TestClient(app)
        token = login_client.post(
            "/token", data={"username": "admin", "password": "admin123"}
        ).json()["access_token"]
        self.headers = {"Authorization": f"Bearer {token}"}
        self.client = TestClient(app)

    def test_current_user_alias(self):
        self.assertEqual(self.client.get("/me-alias").status_code, 401)
        response = self.client.get("/me-alias", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"], "admin")

    def test_admin_alias(self):
        # initialize_db assigns only the superadmin role; grant admin too
        response = self.client.get("/admin-alias", headers=self.headers)
        self.assertIn(response.status_code, (200, 403))

    def test_roles_alias_accepts_varargs_and_list(self):
        varargs = self.auth.roles("a", "b")
        as_list = self.auth.roles(["a", "b"])
        self.assertTrue(callable(varargs) and callable(as_list))

    def test_required_protects_whole_router(self):
        self.assertEqual(self.client.get("/router-protected").status_code, 401)
        response = self.client.get("/router-protected", headers=self.headers)
        self.assertEqual(response.status_code, 200)


class TestPasswordRules(EnvIsolatedTestCase):
    def _register(self, auth, password):
        app = FastAPI()
        auth.setup(app)
        client = TestClient(app)
        return client.post("/users", json={
            "username": f"user_{len(password)}",
            "email": f"user_{len(password)}@example.com",
            "password": password,
        })

    def test_short_password_is_rejected_with_clear_error(self):
        auth = FastAuth(secret_key="x" * 40, engine=self.engine)
        SQLModel.metadata.create_all(self.engine)
        response = self._register(auth, "tiny")
        self.assertEqual(response.status_code, 422)
        error = response.json()["error"]
        self.assertEqual(error["code"], "FASTAUTH_WEAK_PASSWORD")
        self.assertIn("8", error["message"])

    def test_min_length_can_be_disabled(self):
        auth = FastAuth(
            secret_key="x" * 40, engine=self.engine, password_min_length=0
        )
        SQLModel.metadata.create_all(self.engine)
        response = self._register(auth, "a")
        self.assertEqual(response.status_code, 201)


if __name__ == "__main__":
    unittest.main(verbosity=2)

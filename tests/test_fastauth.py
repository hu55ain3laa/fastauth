#!/usr/bin/env python3
"""
Comprehensive test suite for FastAuth library functionality.

Run with: pytest tests/ -v
"""
import os
import tempfile
import unittest

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from fastauth import (
    CredentialsException,
    FastAuth,
    InactiveUserException,
    PasswordManager,
    PermissionDeniedException,
    RefreshTokenException,
    Role,
    RoleNotFoundException,
    TokenException,
    TokenManager,
    User,
    UserExistsException,
    UserNotFoundException,
    UserRole,
)


class TestFastAuth(unittest.TestCase):
    """Test suite for FastAuth library"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        cls.db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        cls.db_url = f"sqlite:///{cls.db_file.name}"

        cls.engine = create_engine(cls.db_url, connect_args={"check_same_thread": False})
        cls.app = FastAPI()

        cls.auth = FastAuth(
            secret_key="test-secret-key-for-fastauth-testing",
            algorithm="HS256",
            user_model=User,
            engine=cls.engine,
            use_cookie=True,
            token_url="/token",
            access_token_expires_in=30,  # minutes
            refresh_token_expires_in=7,  # days
        )

        def get_session():
            with Session(cls.engine) as session:
                yield session

        cls.get_session = get_session

        SQLModel.metadata.create_all(cls.engine)
        cls.initialize_database()

        # One-call setup: routers + exception handlers
        cls.auth.setup(cls.app, session_getter=get_session)

        # Add test routes with different protection levels
        @cls.app.get("/unprotected")
        def unprotected():
            return {"message": "This is an unprotected route"}

        @cls.app.get("/protected")
        def protected(user=Depends(cls.auth.get_current_active_user_dependency())):
            return {"message": "This is a protected route", "user": user.username}

        @cls.app.get("/admin-only")
        def admin_only(user=Depends(cls.auth.is_admin())):
            return {"message": "This is an admin-only route", "user": user.username}

        @cls.app.get("/any-role")
        def any_role(user=Depends(cls.auth.require_roles(["admin", "premium"]))):
            return {"message": "This requires admin OR premium role", "user": user.username}

        @cls.app.get("/all-roles")
        def all_roles(user=Depends(cls.auth.require_all_roles(["premium", "verified"]))):
            return {"message": "This requires premium AND verified roles", "user": user.username}

        # Routes for exercising the error handling system
        error_routes = {
            "/error/credentials": CredentialsException,
            "/error/token": TokenException,
            "/error/refresh-token": RefreshTokenException,
            "/error/inactive-user": InactiveUserException,
            "/error/user-not-found": UserNotFoundException,
            "/error/user-exists": UserExistsException,
            "/error/role-not-found": RoleNotFoundException,
            "/error/permission-denied": PermissionDeniedException,
        }
        for path, exc_class in error_routes.items():
            def make_route(exc=exc_class):
                def route():
                    raise exc()
                return route
            cls.app.get(path)(make_route())

        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        cls.engine.dispose()
        os.unlink(cls.db_file.name)

    @classmethod
    def initialize_database(cls):
        """Initialize database with test data"""
        with Session(cls.engine) as session:
            roles = {
                "superadmin": "Super administrator with all privileges",
                "admin": "Administrator with management privileges",
                "moderator": "User with content moderation privileges",
                "premium": "Premium tier user",
                "verified": "Verified user",
                "user": "Standard user with basic privileges",
            }

            role_ids = {}
            for role_name, description in roles.items():
                role = Role(name=role_name, description=description)
                session.add(role)
                session.commit()
                session.refresh(role)
                role_ids[role_name] = role.id

            users = [
                {"username": "superadmin", "password": "superadmin123", "roles": ["superadmin", "admin"]},
                {"username": "admin", "password": "admin123", "roles": ["admin"]},
                {"username": "moderator", "password": "mod123", "roles": ["moderator"]},
                {"username": "premium", "password": "premium123", "roles": ["premium"]},
                {"username": "verified", "password": "verified123", "roles": ["verified"]},
                {"username": "premium_verified", "password": "premium_verified123", "roles": ["premium", "verified"]},
                {"username": "regular", "password": "regular123", "roles": ["user"]},
            ]

            for user_data in users:
                hashed_password = cls.auth.get_password_hash(user_data["password"])
                user = User(
                    username=user_data["username"],
                    email=f"{user_data['username']}@example.com",
                    hashed_password=hashed_password,
                    disabled=False,
                )
                session.add(user)
                session.commit()
                session.refresh(user)

                for role_name in user_data["roles"]:
                    session.add(UserRole(user_id=user.id, role_id=role_ids[role_name]))
                session.commit()

    def setUp(self):
        """Each test starts with a clean cookie jar."""
        self.client.cookies.clear()

    def login(self, username, password):
        """Helper: log in and return the token response JSON."""
        response = self.client.post("/token", data={"username": username, "password": password})
        self.assertEqual(response.status_code, 200)
        # Drop the auth cookie so tests exercise header auth explicitly
        self.client.cookies.clear()
        return response.json()

    def auth_headers(self, username, password):
        """Helper: log in and return Authorization headers."""
        token_data = self.login(username, password)
        return {"Authorization": f"Bearer {token_data['access_token']}"}

    def test_01_password_manager(self):
        """Test password manager functionality"""
        password_manager = PasswordManager()
        password = "test_password"
        hashed = password_manager.get_password_hash(password)

        self.assertNotEqual(password, hashed)
        self.assertTrue(password_manager.verify_password(password, hashed))
        self.assertFalse(password_manager.verify_password("wrong_password", hashed))

        # Malformed hashes must not raise, just fail verification
        self.assertFalse(password_manager.verify_password(password, "not-a-real-hash"))

    def test_02_long_passwords(self):
        """Passwords longer than bcrypt's 72-byte limit must still work"""
        password_manager = PasswordManager()
        long_password = "x" * 100
        hashed = password_manager.get_password_hash(long_password)
        self.assertTrue(password_manager.verify_password(long_password, hashed))
        self.assertFalse(password_manager.verify_password("y" * 100, hashed))

    def test_03_token_manager(self):
        """Test token manager functionality"""
        token_manager = TokenManager(
            secret_key="test-secret-key",
            algorithm="HS256",
            access_token_expires_minutes=30,
            refresh_token_expires_days=7,
        )

        data = {"sub": "test_user"}
        access_token = token_manager.create_access_token(data)
        self.assertIsNotNone(access_token)

        payload = token_manager.verify_token(access_token, expected_type="access")
        self.assertEqual(payload.get("sub"), "test_user")

        refresh_token = token_manager.create_refresh_token(data)
        self.assertIsNotNone(refresh_token)

        access_payload = token_manager.verify_token(access_token, expected_type="access")
        refresh_payload = token_manager.verify_token(refresh_token, expected_type="refresh")
        self.assertGreater(refresh_payload.get("exp"), access_payload.get("exp"))

        # Wrong token type must be rejected
        with self.assertRaises(TokenException):
            token_manager.verify_token(access_token, expected_type="refresh")

        # Garbage tokens must be rejected
        with self.assertRaises(TokenException):
            token_manager.verify_token("not-a-token", expected_type="access")

    def test_04_user_authentication(self):
        """Test user authentication endpoints"""
        token_data = self.login("admin", "admin123")
        self.assertIn("access_token", token_data)
        self.assertIn("refresh_token", token_data)
        self.assertEqual(token_data["token_type"], "bearer")

        # Invalid credentials
        response = self.client.post("/token", data={"username": "admin", "password": "wrong_password"})
        self.assertEqual(response.status_code, 401)

        # Token refresh
        response = self.client.post(
            "/token/refresh", json={"refresh_token": token_data["refresh_token"]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())

        # Refresh with a missing body must be a validation error, not a crash
        response = self.client.post("/token/refresh", json={})
        self.assertEqual(response.status_code, 422)

        # Refresh with garbage must be a 401
        response = self.client.post("/token/refresh", json={"refresh_token": "garbage"})
        self.assertEqual(response.status_code, 401)

    def test_05_login_sets_cookie(self):
        """Login must set an expiring HTTP-only cookie when use_cookie=True"""
        response = self.client.post("/token", data={"username": "admin", "password": "admin123"})
        self.assertEqual(response.status_code, 200)
        set_cookie = response.headers.get("set-cookie", "")
        self.assertIn("access_token=", set_cookie)
        self.assertIn("HttpOnly", set_cookie)
        self.assertIn("Max-Age=1800", set_cookie)  # 30 minutes

    def test_06_logout_clears_cookie(self):
        """Logout must clear the access token cookie"""
        response = self.client.post("/logout")
        self.assertEqual(response.status_code, 200)
        set_cookie = response.headers.get("set-cookie", "")
        self.assertIn('access_token=""', set_cookie)

    def test_07_protected_routes(self):
        """Test route protection with authentication"""
        headers = self.auth_headers("admin", "admin123")

        response = self.client.get("/unprotected")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/protected")
        self.assertEqual(response.status_code, 401)

        response = self.client.get("/protected", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"], "admin")

    def test_08_role_based_authorization(self):
        """Test role-based authorization"""
        admin_headers = self.auth_headers("admin", "admin123")
        response = self.client.get("/admin-only", headers=admin_headers)
        self.assertEqual(response.status_code, 200)

        regular_headers = self.auth_headers("regular", "regular123")
        response = self.client.get("/admin-only", headers=regular_headers)
        self.assertEqual(response.status_code, 403)

        premium_headers = self.auth_headers("premium", "premium123")
        response = self.client.get("/any-role", headers=premium_headers)
        self.assertEqual(response.status_code, 200)

        premium_verified_headers = self.auth_headers("premium_verified", "premium_verified123")
        response = self.client.get("/all-roles", headers=premium_verified_headers)
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/all-roles", headers=premium_headers)
        self.assertEqual(response.status_code, 403)

    def test_09_role_management_api(self):
        """Test role management API endpoints"""
        headers = self.auth_headers("superadmin", "superadmin123")

        # List all roles
        response = self.client.get("/roles/", headers=headers)
        self.assertEqual(response.status_code, 200)
        roles = response.json()
        self.assertIsInstance(roles, list)
        self.assertGreaterEqual(len(roles), 6)

        # Create a new role
        response = self.client.post(
            "/roles/", headers=headers, json={"name": "test_role", "description": "A test role"}
        )
        self.assertEqual(response.status_code, 201)
        created_role = response.json()
        self.assertEqual(created_role["name"], "test_role")
        role_id = created_role["id"]

        # Creating a duplicate role must fail cleanly
        response = self.client.post(
            "/roles/", headers=headers, json={"name": "test_role", "description": "dup"}
        )
        self.assertEqual(response.status_code, 409)

        # Get role by ID
        response = self.client.get(f"/roles/{role_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "test_role")

        with Session(self.engine) as session:
            user = session.exec(select(User).where(User.username == "regular")).first()
            user_id = user.id

        # Assign role to user
        response = self.client.post(f"/roles/assign/{user_id}/{role_id}", headers=headers)
        self.assertEqual(response.status_code, 200)

        # Get user roles
        response = self.client.get(f"/roles/user/{user_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        role_names = [role["name"] for role in response.json()]
        self.assertIn("test_role", role_names)

        # Remove role from user
        response = self.client.delete(f"/roles/assign/{user_id}/{role_id}", headers=headers)
        self.assertEqual(response.status_code, 200)

        # Delete the role
        response = self.client.delete(f"/roles/{role_id}", headers=headers)
        self.assertEqual(response.status_code, 204)

    def test_10_user_me_endpoint(self):
        """Test the /users/me endpoint"""
        headers = self.auth_headers("admin", "admin123")
        response = self.client.get("/users/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        user_info = response.json()
        self.assertEqual(user_info["username"], "admin")
        self.assertEqual(user_info["email"], "admin@example.com")
        self.assertIn("id", user_info)
        self.assertNotIn("hashed_password", user_info)

    def test_11_user_registration(self):
        """Test user registration endpoint"""
        new_user = {
            "username": "new_test_user",
            "email": "new_test_user@example.com",
            "password": "test_password",
        }
        response = self.client.post("/users", json=new_user)
        self.assertEqual(response.status_code, 201)
        created_user = response.json()
        self.assertEqual(created_user["username"], "new_test_user")
        self.assertNotIn("hashed_password", created_user)

        # Log in with the new user
        self.login("new_test_user", "test_password")

        # Duplicate username -> 409
        response = self.client.post("/users", json={
            "username": "new_test_user",
            "email": "another_email@example.com",
            "password": "another_password",
        })
        self.assertEqual(response.status_code, 409)

        # Duplicate email -> 409 (not an internal server error)
        response = self.client.post("/users", json={
            "username": "different_user",
            "email": "new_test_user@example.com",
            "password": "another_password",
        })
        self.assertEqual(response.status_code, 409)

        # Regression: a failed registration must not poison later requests
        self.login("new_test_user", "test_password")

    def test_12_disabled_user(self):
        """Disabled users must not be able to log in, refresh, or access routes"""
        # Create and log in while enabled
        response = self.client.post("/users", json={
            "username": "soon_disabled",
            "email": "soon_disabled@example.com",
            "password": "pw123456",
        })
        self.assertEqual(response.status_code, 201)
        token_data = self.login("soon_disabled", "pw123456")

        # Disable the user
        with Session(self.engine) as session:
            user = session.exec(select(User).where(User.username == "soon_disabled")).first()
            user.disabled = True
            session.add(user)
            session.commit()

        headers = {"Authorization": f"Bearer {token_data['access_token']}"}

        # Existing access token must be rejected by active-user routes
        response = self.client.get("/protected", headers=headers)
        self.assertEqual(response.status_code, 403)

        # Refresh token must be rejected
        response = self.client.post(
            "/token/refresh", json={"refresh_token": token_data["refresh_token"]}
        )
        self.assertEqual(response.status_code, 403)

        # New login must be rejected
        response = self.client.post(
            "/token", data={"username": "soon_disabled", "password": "pw123456"}
        )
        self.assertEqual(response.status_code, 403)

    def test_13_error_handling(self):
        """Test the standardized error handling system"""
        expected = {
            "/error/credentials": (401, "FASTAUTH_INVALID_CREDENTIALS"),
            "/error/token": (401, "FASTAUTH_INVALID_TOKEN"),
            "/error/refresh-token": (401, "FASTAUTH_INVALID_REFRESH_TOKEN"),
            "/error/inactive-user": (403, "FASTAUTH_INACTIVE_USER"),
            "/error/user-not-found": (404, "FASTAUTH_USER_NOT_FOUND"),
            "/error/user-exists": (409, "FASTAUTH_USER_EXISTS"),
            "/error/role-not-found": (404, "FASTAUTH_ROLE_NOT_FOUND"),
            "/error/permission-denied": (403, "FASTAUTH_PERMISSION_DENIED"),
        }

        for endpoint, (status_code, error_code) in expected.items():
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status_code, endpoint)
            error_data = response.json()
            self.assertIn("error", error_data, endpoint)
            self.assertEqual(error_data["error"]["code"], error_code, endpoint)
            self.assertIn("message", error_data["error"], endpoint)
            self.assertEqual(error_data["error"]["status_code"], status_code, endpoint)


if __name__ == "__main__":
    unittest.main(verbosity=2)

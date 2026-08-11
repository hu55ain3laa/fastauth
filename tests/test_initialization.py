"""Tests for database initialization and superadmin creation."""
import os
import tempfile
import unittest

from sqlmodel import Session, create_engine, select

from fastauth import FastAuth, Role, User


class TestInitialization(unittest.TestCase):
    """Test initialize_db and create_superadmin."""

    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.engine = create_engine(f"sqlite:///{self.db_file.name}")
        self.auth = FastAuth(secret_key="init-test-secret", engine=self.engine)

    def tearDown(self):
        self.engine.dispose()
        os.unlink(self.db_file.name)

    def test_initialize_db_creates_everything(self):
        results = self.auth.initialize_db(
            admin_username="boss",
            admin_password="boss-password",
        )

        self.assertTrue(results["tables_created"])
        self.assertTrue(results["roles_initialized"])
        self.assertTrue(results["superadmin_created"])
        self.assertEqual(results["superadmin_username"], "boss")
        self.assertTrue(results["superadmin_is_new"])

        with Session(self.engine) as session:
            role_names = {r.name for r in session.exec(select(Role)).all()}
            self.assertLessEqual(
                {"superadmin", "admin", "moderator", "premium", "verified", "user"},
                role_names,
            )
            user = session.exec(select(User).where(User.username == "boss")).first()
            self.assertIsNotNone(user)

        # The superadmin's password must actually work
        authenticated = self.auth.authenticate_user("boss", "boss-password")
        self.assertNotEqual(authenticated, False)

    def test_create_superadmin_is_idempotent(self):
        self.auth.initialize_db(admin_username="boss", admin_password="boss-password")

        # Second call must report the existing superadmin, not a new one
        info = self.auth.create_superadmin(username="boss", password="boss-password")
        self.assertFalse(info["is_new"])
        self.assertEqual(info["username"], "boss")


if __name__ == "__main__":
    unittest.main(verbosity=2)

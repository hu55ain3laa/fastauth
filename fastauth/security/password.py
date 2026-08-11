import bcrypt


class PasswordManager:
    """Handles password hashing and verification using bcrypt."""

    def __init__(self, rounds: int = 12):
        """Initialize the password manager.

        Args:
            rounds: bcrypt work factor (cost). Higher is slower and safer.
        """
        self.rounds = rounds

    @staticmethod
    def _to_bytes(password: str) -> bytes:
        # bcrypt only uses the first 72 bytes of a password; truncate explicitly
        # so longer passwords keep working instead of raising ValueError.
        return password.encode("utf-8")[:72]

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password.

        Args:
            plain_password: The plain text password to verify
            hashed_password: The hashed password to compare against

        Returns:
            bool: True if the password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                self._to_bytes(plain_password),
                hashed_password.encode("utf-8"),
            )
        except ValueError:
            # Malformed/unknown hash format
            return False

    def get_password_hash(self, password: str) -> str:
        """Hash a password with bcrypt.

        Args:
            password: The plain text password to hash

        Returns:
            str: The hashed password
        """
        return bcrypt.hashpw(
            self._to_bytes(password),
            bcrypt.gensalt(rounds=self.rounds),
        ).decode("utf-8")

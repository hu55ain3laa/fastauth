from passlib.context import CryptContext


class PasswordManager:
    """Handles password hashing and verification."""
    
    def __init__(self, schemes=["bcrypt"], deprecated="auto"):
        """Initialize the password manager with specified hashing schemes.
        
        Args:
            schemes: List of hashing schemes to use
            deprecated: Handling method for deprecated schemes
        """
        self.pwd_context = CryptContext(schemes=schemes, deprecated=deprecated)
    
    def verify_password(self, plain_password, hashed_password):
        """Verify a plain password against a hashed password.
        
        Args:
            plain_password: The plain text password to verify
            hashed_password: The hashed password to compare against
            
        Returns:
            bool: True if the password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password):
        """Hash a password using configured algorithms.
        
        Args:
            password: The plain text password to hash
            
        Returns:
            str: The hashed password
        """
        return self.pwd_context.hash(password)

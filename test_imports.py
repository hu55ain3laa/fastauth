# Test script to verify imports and basic functionality
print("Testing FastAuth import functionality...")

# Test the main imports
try:
    from fastauth import FastAuth, User, Token, TokenData
    print("✅ Successfully imported main components")
except Exception as e:
    print(f"❌ Error importing main components: {e}")
    
# Test module-specific imports
try:
    from fastauth.security.password import PasswordManager
    from fastauth.security.tokens import TokenManager
    print("✅ Successfully imported security modules")
except Exception as e:
    print(f"❌ Error importing security modules: {e}")

try:
    from fastauth.models.user import User, UserCreate
    from fastauth.models.tokens import Token
    print("✅ Successfully imported model modules")
except Exception as e:
    print(f"❌ Error importing model modules: {e}")
    
try:
    from fastauth.dependencies.auth import AuthDependencies
    print("✅ Successfully imported dependency modules")
except Exception as e:
    print(f"❌ Error importing dependency modules: {e}")
    
try:
    from fastauth.routers.auth import AuthRouter
    print("✅ Successfully imported router modules")
except Exception as e:
    print(f"❌ Error importing router modules: {e}")

# Test basic class instantiation
try:
    # We can't fully test without a database engine, but we can check class creation
    password_manager = PasswordManager()
    hashed = password_manager.get_password_hash("test_password")
    verified = password_manager.verify_password("test_password", hashed)
    print(f"✅ Successfully tested password manager functionality: {verified}")
except Exception as e:
    print(f"❌ Error testing password manager: {e}")

print("\nTesting complete!")

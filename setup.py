from setuptools import setup, find_packages

setup(
    name="fastauth_iq",
    version="0.1.6",
    packages=find_packages(),  # This will find all packages, including fastauth_iq
    py_modules=["fastauth", "User"],  # Include module files at root level
    install_requires=[
        "fastapi>=0.104.0",
        "sqlmodel>=0.0.8",
        "pydantic>=2.5.2",
        "passlib[bcrypt]>=1.7.4", 
        "python-jose[cryptography]>=3.3.0",
        "python-multipart>=0.0.6",
        "pyjwt>=2.6.0",
    ],
    author="Hussein Ghadhban",
    author_email="ala.1995@yahoo.com",
    description="A comprehensive authentication library for FastAPI with JWT and cookie support",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/hu55ain3laa/fastauth",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Framework :: FastAPI",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Session",
    ],
    keywords=["fastapi", "authentication", "jwt", "oauth2", "sqlmodel", "token"],
    python_requires=">=3.9",
)

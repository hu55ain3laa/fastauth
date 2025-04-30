from setuptools import setup, find_packages

setup(
    name="fastauth_iq",
    version="0.1.0",
    packages=["fastauth"],  # Explicitly include fastauth package
    package_dir={"fastauth": "."},  # Point to the current directory for fastauth package
    package_data={"fastauth": ["*.py"]},  # Include all .py files
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
    author="FastAuth Developer",
    author_email="your.email@example.com",
    description="A comprehensive authentication library for FastAPI with JWT and cookie support",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/hu55ain3laa/fastauth",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: FastAPI",
    ],
    python_requires=">=3.8",
)

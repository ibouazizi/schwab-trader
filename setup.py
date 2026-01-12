from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="schwab-trader",
    version="1.0.1",
    author="Imed Bouazizi",
    author_email="vidoptdev@gmail.com",
    description="A Python library for interacting with Charles Schwab's Trading API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ibouazizi/schwab-trader",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=9.0.0",
            "pytest-asyncio>=1.3.0",
            "pytest-cov>=7.0.0",
            "black>=25.1.0",
            "isort>=6.0.0",
            "mypy>=1.15.0",
            "build>=1.4.0",
            "twine>=6.2.0",
        ],
    },
)

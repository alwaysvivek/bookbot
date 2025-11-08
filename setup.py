from setuptools import setup, find_packages

setup(
    name="bookbot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "aiosqlite>=0.19.0",
        "scikit-learn>=1.3.0",
        "numpy>=1.24.0",
        "rapidfuzz>=3.5.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "httpx>=0.25.0",
        ],
    },
)

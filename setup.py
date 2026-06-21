#!/usr/bin/env python3
"""XiaoQi SecPilot — AI-driven security knowledge copilot for penetration testers."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="xiaoqi-sec-pilot",
    version="1.0.0",
    author="XiaoQiWUMI",
    author_email="401817506@qq.com",
    description="AI-driven security knowledge copilot — instant lookup of bypass techniques, "
                "attack methodologies, WAF fingerprints, default credentials, and more.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/XiaoQiWUMI/XiaoQi-SecPilot",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "rich>=13.0.0",
        "click>=8.0.0",
        "pyyaml>=6.0",
        "thefuzz>=0.20.0",
        "python-Levenshtein>=0.21.0",
    ],
    entry_points={
        "console_scripts": [
            "secpilot=sec_pilot.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
    ],
    python_requires=">=3.9",
)

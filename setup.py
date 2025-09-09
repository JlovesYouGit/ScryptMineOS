#!/usr/bin/env python3
"""
ScryptMineOS Setup Configuration
Advanced ASIC Mining Simulation Platform
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements from requirements.txt
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    
    requirements = []
    dev_requirements = []
    in_dev_section = False
    
    for line in lines:
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        if line == "[dev]":
            in_dev_section = True
            continue
        
        if in_dev_section:
            dev_requirements.append(line)
        else:
            requirements.append(line)
    
    return requirements, dev_requirements

requirements, dev_requirements = read_requirements()

setup(
    name="scryptmineos",
    version="2.1.0",
    author="ScryptMineOS Development Team",
    author_email="dev@scryptmineos.org",
    description="Advanced ASIC Mining Simulation Platform",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/JlovesYouGit/ScryptMineOS",
    project_urls={
        "Bug Tracker": "https://github.com/JlovesYouGit/ScryptMineOS/issues",
        "Documentation": "https://github.com/JlovesYouGit/ScryptMineOS/wiki",
        "Source Code": "https://github.com/JlovesYouGit/ScryptMineOS",
        "Security Policy": "https://github.com/JlovesYouGit/ScryptMineOS/security/policy",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: System :: Distributed Computing",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Natural Language :: English",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "docs": [
            "sphinx>=4.0.0,<8.0.0",
            "sphinx-rtd-theme>=1.0.0,<3.0.0",
            "myst-parser>=0.17.0,<3.0.0",
        ],
        "testing": [
            "pytest>=6.2.0,<8.0.0",
            "pytest-cov>=2.12.0,<5.0.0",
            "pytest-asyncio>=0.18.0,<1.0.0",
            "factory-boy>=3.2.0,<4.0.0",
            "faker>=13.0.0,<20.0.0",
            "responses>=0.18.0,<1.0.0",
        ],
        "security": [
            "bandit>=1.7.0,<2.0.0",
            "safety>=2.0.0,<4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "scryptmineos=scryptmineos.cli:main",
            "scryptmine=scryptmineos.cli:main",  # Short alias
        ],
    },
    include_package_data=True,
    package_data={
        "scryptmineos": [
            "data/*.json",
            "data/*.yaml",
            "templates/*.yaml",
            "profiles/*.json",
        ],
    },
    zip_safe=False,
    keywords=[
        "mining",
        "simulation",
        "asic",
        "cryptocurrency",
        "blockchain",
        "scrypt",
        "litecoin",
        "dogecoin",
        "testing",
        "research",
        "education",
    ],
    platforms=["any"],
    license="GPL-3.0",
    license_files=["LICENSE"],
)

# -*- coding: utf-8 -*-

# Copyright EHS authors. All rights reserved.
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.

from setuptools import setup, find_packages
import codecs


README = codecs.open("README.md", encoding="utf-8").read()

setup(
    name="ehs",
    version="1.0.0",
    description="Extended Historian Service for the Arrowhead Framework",
    long_description=README,
    author="Mario Thron",
    license="MIT License",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=["PyYAML", "jsonschema", "grpcio-tools", "cmd2"],
    extras_require={
        "server": ["pykka", "apscheduler", "SQLAlchemy"],
        "configurator": ["PySide6", "deepdiff"],
        "arrowhead": ["arrowhead-client"],
        "application": ["matplotlib"],
    },
    python_requires=">=3.10",
)

#!/usr/bin/env python

from setuptools import setup

setup(
    name="nosepipe",
    version="0.2a",
    download_url = "http://pypi.python.org/pypi/nosepipe/",

    description = "Plugin for the nose testing framework for running tests in "
                  "a subprocess",
    author = "John J. Lee",
    author_email = "jjl@pobox.com",
    license = "BSD",
    platforms = ["any"],

    install_requires = ["nose>=0.1.0, ==dev"],

    url = "http://pypi.python.org/pypi/nosepipe/",

    long_description = """\
Plugin for the nose testing framework for running tests in a subprocess.

Use ``nosetests --with-process-isolation`` to enable the plugin.  When enabled,
each test is run in a separate process.
""",

    py_modules = ["nosepipe"],
    entry_points = {
        "nose.plugins.0.10": [
            "process-isolation = nosepipe:ProcessIsolationPlugin",
            "process-isolation-reporter = "
                "nosepipe:ProcessIsolationReporterPlugin"]
        },
    zip_safe = True,
)

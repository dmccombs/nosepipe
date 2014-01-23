#!/usr/bin/env python

from setuptools import setup

setup(
    name="nosepipe",
    version="0.3",
    download_url = "http://pypi.python.org/pypi/nosepipe/",

    description = "Plugin for the nose testing framework for running tests in "
                  "a subprocess",
    author = "John J. Lee, Dan McCombs",
    author_email = "dmccombs@dyn.com",
    license = "BSD",
    platforms = ["any"],

    install_requires = ["nose>=0.1.0, ==dev"],

    url = "http://github.com/dmccombs/nosepipe/",

    long_description = """\
Plugin for the nose testing framework for running tests in a subprocess.

Use ``nosetests --with-process-isolation`` to enable the plugin.  When enabled,
each test is run in a separate process.

Supports Python 2 and 3.
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

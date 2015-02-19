#!/usr/bin/env python

from setuptools import setup

setup(
    name="nosepipe",
    version="0.6",
    download_url = "http://pypi.python.org/pypi/nosepipe/",

    description = "Plugin for the nose testing framework for running tests in "
                  "a subprocess",
    author = "John J. Lee, Dan McCombs, Vadim Markovtsev",
    author_email = "dmccombs@dyn.com",
    license = "BSD",
    platforms = ["any"],

    install_requires = ["nose>=0.1.0"],

    url = "http://github.com/dmccombs/nosepipe/",

    long_description = """\
Plugin for the nose testing framework for running tests in a subprocess.

Use ``nosetests --with-process-isolation`` to enable the plugin.  When enabled,
each test is run in a separate process.

Additionally add the ``--with-process-isolation-individual`` option and decorate
top level test functions or classes with ``@nosepipe.isolate`` to only run those
tests in isolation.

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
